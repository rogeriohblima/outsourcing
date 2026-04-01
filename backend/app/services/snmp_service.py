"""
services/snmp_service.py — Serviço de leitura de contadores via SNMP.

Tenta ler o contador de páginas impressas de uma impressora de rede
usando SNMP v2c. Se a leitura automática falhar, o sistema permite
o lançamento manual do contador pelo fiscal.

OIDs tentados (por ordem de prioridade):
  1. RFC 3805 padrão    : 1.3.6.1.2.1.43.10.2.1.4.1.1 (prtMarkerLifeCount)
  2. HP                 : 1.3.6.1.4.1.11.2.3.9.4.2.1.4.1.2.6.0
  3. Xerox              : 1.3.6.1.4.1.253.8.53.13.2.1.6.1.20.1
  4. Ricoh              : 1.3.6.1.4.1.367.3.2.1.2.19.5.1.5.1
  5. Canon              : 1.3.6.1.4.1.1602.1.11.1.3.1.4.301
  6. Lexmark            : 1.3.6.1.4.1.641.2.1.2.1.6.1
  7. Samsung/HP         : 1.3.6.1.4.1.236.11.5.11.55.1.0
  8. Brother            : 1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.8.0
"""

import logging
from dataclasses import dataclass
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# OIDs para leitura de contadores totais de impressão
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


async def ler_contador_snmp(ip: str) -> SNMPResultado:
    """
    Lê o contador total de páginas de uma impressora via SNMP v2c.

    Tenta cada OID da lista OIDS_CONTADOR_TOTAL em sequência até
    obter uma resposta válida. Retorna o primeiro contador encontrado.

    Args:
        ip: Endereço IP da impressora

    Returns:
        SNMPResultado com sucesso=True e o contador, ou sucesso=False com erro.
    """
    try:
        # Importação lazy para não bloquear se pysnmp não estiver instalado
        from pysnmp.hlapi.asyncio import (
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            getCmd,
        )

        engine = SnmpEngine()
        community = CommunityData(settings.SNMP_COMMUNITY, mpModel=1)  # v2c
        target = UdpTransportTarget(
            (ip, settings.SNMP_PORT),
            timeout=settings.SNMP_TIMEOUT,
            retries=settings.SNMP_RETRIES,
        )

        for fabricante, oid in OIDS_CONTADOR_TOTAL:
            try:
                iterator = getCmd(
                    engine,
                    community,
                    target,
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                )
                errIndication, errStatus, errIndex, varBinds = await iterator

                if errIndication:
                    logger.debug(
                        "SNMP [%s] OID %s (%s): %s",
                        ip, oid, fabricante, errIndication,
                    )
                    continue

                if errStatus:
                    logger.debug(
                        "SNMP [%s] OID %s (%s): status de erro %s",
                        ip, oid, fabricante, errStatus.prettyPrint(),
                    )
                    continue

                for varBind in varBinds:
                    valor = int(varBind[1])
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
                logger.debug("SNMP [%s] OID %s (%s) falhou: %s", ip, oid, fabricante, exc)
                continue

        return SNMPResultado(
            sucesso=False,
            erro=(
                f"Nenhum OID retornou um contador válido para {ip}. "
                "Verifique community string, IP e se o agente SNMP está ativo."
            ),
        )

    except ImportError:
        return SNMPResultado(
            sucesso=False,
            erro="Biblioteca pysnmp não instalada. Execute: pip install pysnmp",
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Erro inesperado ao ler SNMP de %s: %s", ip, exc)
        return SNMPResultado(sucesso=False, erro=str(exc))


async def testar_conectividade_snmp(ip: str) -> dict:
    """
    Testa a conectividade SNMP com a impressora lendo o sysDescr (OID padrão).

    Útil para diagnosticar problemas de rede/SNMP sem tentar ler contadores.

    Returns:
        dict com 'acessivel' (bool), 'descricao' e 'erro' (se houver)
    """
    try:
        from pysnmp.hlapi.asyncio import (
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            getCmd,
        )

        engine = SnmpEngine()
        community = CommunityData(settings.SNMP_COMMUNITY, mpModel=1)
        target = UdpTransportTarget(
            (ip, settings.SNMP_PORT),
            timeout=settings.SNMP_TIMEOUT,
            retries=1,
        )

        iterator = getCmd(
            engine,
            community,
            target,
            ContextData(),
            ObjectType(ObjectIdentity("1.3.6.1.2.1.1.1.0")),  # sysDescr
        )
        errIndication, errStatus, errIndex, varBinds = await iterator

        if errIndication:
            return {"acessivel": False, "descricao": None, "erro": str(errIndication)}

        descricao = str(varBinds[0][1]) if varBinds else "N/A"
        return {"acessivel": True, "descricao": descricao, "erro": None}

    except Exception as exc:  # noqa: BLE001
        return {"acessivel": False, "descricao": None, "erro": str(exc)}
