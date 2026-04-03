"""
services/snmp_service.py — Servico de leitura de contadores via SNMP.

Usa a API classica do pysnmp 4.4.12 (hlapi sincrono), executada dentro
de asyncio.to_thread() para nao bloquear o event loop do FastAPI.

Por que pysnmp 4.4.12 e nao 6.x/7.x?
  A versao 6.x declara dependencia de pytest-cov<5.0, conflitando com
  versoes modernas do pytest. A versao 4.4.12 nao tem essa restricao e
  e amplamente compativel com Python 3.11+.

OIDs tentados (por ordem de prioridade):
  1. RFC 3805 padrao    : 1.3.6.1.2.1.43.10.2.1.4.1.1 (prtMarkerLifeCount)
  2. HP                 : 1.3.6.1.4.1.11.2.3.9.4.2.1.4.1.2.6.0
  3. Xerox              : 1.3.6.1.4.1.253.8.53.13.2.1.6.1.20.1
  4. Ricoh              : 1.3.6.1.4.1.367.3.2.1.2.19.5.1.5.1
  5. Canon              : 1.3.6.1.4.1.1602.1.11.1.3.1.4.301
  6. Lexmark            : 1.3.6.1.4.1.641.2.1.2.1.6.1
  7. Samsung/HP         : 1.3.6.1.4.1.236.11.5.11.55.1.0
  8. Brother            : 1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.8.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# OIDs para leitura de contadores totais de impressao
OIDS_CONTADOR_TOTAL = [
    ("RFC3805_Standard", "1.3.6.1.2.1.43.10.2.1.4.1.1"),
    ("HP_PageCount",     "1.3.6.1.4.1.11.2.3.9.4.2.1.4.1.2.6.0"),
    ("Xerox_Impressions","1.3.6.1.4.1.253.8.53.13.2.1.6.1.20.1"),
    ("Ricoh_TotalCount", "1.3.6.1.4.1.367.3.2.1.2.19.5.1.5.1"),
    ("Canon_Counter",    "1.3.6.1.4.1.1602.1.11.1.3.1.4.301"),
    ("Lexmark_Counter",  "1.3.6.1.4.1.641.2.1.2.1.6.1"),
    ("Samsung_Counter",  "1.3.6.1.4.1.236.11.5.11.55.1.0"),
    ("Brother_Counter",  "1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.8.0"),
]


@dataclass
class SNMPResultado:
    """Resultado de uma tentativa de leitura SNMP."""
    sucesso: bool
    contador: Optional[int] = None
    oid_usado: Optional[str] = None
    fabricante_detectado: Optional[str] = None
    erro: Optional[str] = None


def _ler_snmp_sincrono(ip: str, community: str, port: int,
                       timeout: int, retries: int) -> SNMPResultado:
    """
    Leitura SNMP usando a API classica (sincrona) do pysnmp 4.4.12.

    Esta funcao e bloqueante e deve ser chamada via asyncio.to_thread().

    Args:
        ip       : Endereco IP da impressora
        community: Community string SNMP (ex: 'public')
        port     : Porta UDP (padrao 161)
        timeout  : Timeout em segundos por OID
        retries  : Numero de tentativas por OID

    Returns:
        SNMPResultado com o primeiro contador valido encontrado.
    """
    try:
        from pysnmp.hlapi import (
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            getCmd,
        )
    except ImportError:
        return SNMPResultado(
            sucesso=False,
            erro="Biblioteca pysnmp nao instalada. Execute: pip install pysnmp==4.4.12",
        )

    engine = SnmpEngine()

    for fabricante, oid in OIDS_CONTADOR_TOTAL:
        try:
            error_indication, error_status, error_index, var_binds = next(
                getCmd(
                    engine,
                    CommunityData(community, mpModel=1),  # SNMPv2c
                    UdpTransportTarget(
                        (ip, port),
                        timeout=timeout,
                        retries=retries,
                    ),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                )
            )

            if error_indication:
                logger.debug(
                    "SNMP [%s] OID %s (%s): %s",
                    ip, oid, fabricante, error_indication,
                )
                continue

            if error_status:
                logger.debug(
                    "SNMP [%s] OID %s (%s): status de erro %s em %s",
                    ip, oid, fabricante,
                    error_status.prettyPrint(),
                    error_index and var_binds[int(error_index) - 1][0] or "?",
                )
                continue

            for var_bind in var_binds:
                try:
                    valor = int(var_bind[1])
                except (TypeError, ValueError):
                    continue

                if valor > 0:
                    logger.info(
                        "SNMP [%s] Contador lido via OID %s (%s): %d",
                        ip, oid, fabricante, valor,
                    )
                    return SNMPResultado(
                        sucesso=True,
                        contador=valor,
                        oid_usado=oid,
                        fabricante_detectado=fabricante,
                    )

        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "SNMP [%s] OID %s (%s) falhou: %s",
                ip, oid, fabricante, exc,
            )
            continue

    return SNMPResultado(
        sucesso=False,
        erro=(
            f"Nenhum OID retornou contador valido para {ip}. "
            "Verifique IP, community string e se o agente SNMP esta ativo."
        ),
    )


def _testar_conectividade_sincrono(ip: str, community: str,
                                   port: int, timeout: int) -> dict:
    """
    Testa conectividade SNMP lendo o sysDescr (OID padrao 1.3.6.1.2.1.1.1.0).
    Funcao sincrona — chamar via asyncio.to_thread().
    """
    try:
        from pysnmp.hlapi import (
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            getCmd,
        )

        engine = SnmpEngine()
        error_indication, error_status, _, var_binds = next(
            getCmd(
                engine,
                CommunityData(community, mpModel=1),
                UdpTransportTarget((ip, port), timeout=timeout, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity("1.3.6.1.2.1.1.1.0")),  # sysDescr
            )
        )

        if error_indication:
            return {"acessivel": False, "descricao": None, "erro": str(error_indication)}

        descricao = str(var_binds[0][1]) if var_binds else "N/A"
        return {"acessivel": True, "descricao": descricao, "erro": None}

    except Exception as exc:  # noqa: BLE001
        return {"acessivel": False, "descricao": None, "erro": str(exc)}


# ── API Assincrona (wrappers) ─────────────────────────────────────────────────

async def ler_contador_snmp(ip: str) -> SNMPResultado:
    """
    Lê o contador total de paginas de uma impressora via SNMP v2c.

    Executa a leitura sincrona em uma thread separada para nao bloquear
    o event loop do FastAPI (asyncio.to_thread).

    Args:
        ip: Endereco IP da impressora

    Returns:
        SNMPResultado com sucesso=True e o contador, ou sucesso=False com erro.
    """
    try:
        resultado = await asyncio.to_thread(
            _ler_snmp_sincrono,
            ip,
            settings.SNMP_COMMUNITY,
            settings.SNMP_PORT,
            settings.SNMP_TIMEOUT,
            settings.SNMP_RETRIES,
        )
        return resultado
    except Exception as exc:  # noqa: BLE001
        logger.error("Erro inesperado ao executar SNMP para %s: %s", ip, exc)
        return SNMPResultado(sucesso=False, erro=str(exc))


async def testar_conectividade_snmp(ip: str) -> dict:
    """
    Testa se a impressora esta acessivel via SNMP.

    Returns:
        dict com 'acessivel' (bool), 'descricao' e 'erro' (se houver)
    """
    try:
        return await asyncio.to_thread(
            _testar_conectividade_sincrono,
            ip,
            settings.SNMP_COMMUNITY,
            settings.SNMP_PORT,
            settings.SNMP_TIMEOUT,
        )
    except Exception as exc:  # noqa: BLE001
        return {"acessivel": False, "descricao": None, "erro": str(exc)}