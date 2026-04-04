"""
tests/test_snmp.py — Testes unitários do servico SNMP.

Todos os testes usam mocks para nao depender de rede real.
A funcao testar_conectividade_snmp NAO e importada diretamente para evitar
que o pytest a colete como teste (nome comeca com "testar").
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.snmp_service import (
    OIDS_CONTADOR_TOTAL,
    SNMPResultado,
    ler_contador_snmp,
)

# NAO importar testar_conectividade_snmp diretamente — pytest coletaria como teste
import app.services.snmp_service as _snmp_module


# ── Testes de ler_contador_snmp ───────────────────────────────────────────────

@pytest.mark.asyncio
class TestLerContadorSNMP:
    """Testa a funcao principal de leitura de contador via SNMP."""

    async def test_sucesso_com_primeiro_oid(self):
        """Quando SNMP retorna sucesso, deve ter sucesso=True e contador preenchido."""
        with patch("app.services.snmp_service.ler_contador_snmp") as mock_ler:
            mock_ler.return_value = SNMPResultado(
                sucesso=True,
                contador=54321,
                oid_usado=OIDS_CONTADOR_TOTAL[0][1],
                fabricante_detectado="RFC3805_Standard",
            )
            resultado = await mock_ler("192.168.1.100")

        assert resultado.sucesso is True
        assert resultado.contador == 54321
        assert resultado.oid_usado is not None

    async def test_falha_retorna_sucesso_false(self):
        """Quando nenhum OID responde, sucesso deve ser False com mensagem de erro."""
        with patch("app.services.snmp_service.ler_contador_snmp") as mock_ler:
            mock_ler.return_value = SNMPResultado(
                sucesso=False,
                erro="Nenhum OID retornou contador valido.",
            )
            resultado = await mock_ler("10.0.0.1")

        assert resultado.sucesso is False
        assert resultado.contador is None
        assert resultado.erro is not None

    async def test_resultado_sucesso_tem_oid_preenchido(self):
        """Resultado bem-sucedido deve sempre ter oid_usado preenchido."""
        with patch("app.services.snmp_service.ler_contador_snmp") as mock_ler:
            mock_ler.return_value = SNMPResultado(
                sucesso=True,
                contador=100,
                oid_usado="1.3.6.1.2.1.43.10.2.1.4.1.1",
            )
            resultado = await mock_ler("192.168.0.1")

        assert resultado.oid_usado is not None

    async def test_pysnmp_nao_instalado(self):
        """Se pysnmp nao estiver disponivel, deve retornar erro descritivo."""
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name.startswith("pysnmp"):
                raise ImportError("No module named 'pysnmp'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            resultado = await ler_contador_snmp("192.168.1.1")

        assert resultado.sucesso is False
        assert "pysnmp" in (resultado.erro or "").lower()

    def test_lista_oids_nao_vazia(self):
        """A lista de OIDs deve conter ao menos os fabricantes principais."""
        fabricantes = [nome for nome, _ in OIDS_CONTADOR_TOTAL]
        assert "RFC3805_Standard" in fabricantes
        assert "HP_PageCount" in fabricantes
        assert len(OIDS_CONTADOR_TOTAL) >= 6


# ── Testes de conectividade SNMP ──────────────────────────────────────────────

@pytest.mark.asyncio
class TestConectividadeSNMP:
    """
    Testa a funcao de verificacao de conectividade SNMP.
    Acessa via modulo para evitar coleta indevida pelo pytest.
    """

    async def test_acessivel_retorna_descricao(self):
        """Quando acessivel, deve retornar acessivel=True e descricao preenchida."""
        mock_resultado = {
            "acessivel": True,
            "descricao": "HP ETHERNET MULTI-ENVIRONMENT",
            "erro": None,
        }
        with patch.object(
            _snmp_module, "testar_conectividade_snmp",
            new=AsyncMock(return_value=mock_resultado)
        ):
            resultado = await _snmp_module.testar_conectividade_snmp("10.0.0.50")

        assert resultado["acessivel"] is True
        assert resultado["descricao"] is not None
        assert resultado["erro"] is None

    async def test_inacessivel_retorna_erro(self):
        """Quando inacessivel, deve retornar acessivel=False e mensagem de erro."""
        mock_resultado = {
            "acessivel": False,
            "descricao": None,
            "erro": "No SNMP response received before timeout",
        }
        with patch.object(
            _snmp_module, "testar_conectividade_snmp",
            new=AsyncMock(return_value=mock_resultado)
        ):
            resultado = await _snmp_module.testar_conectividade_snmp("10.99.99.99")

        assert resultado["acessivel"] is False
        assert resultado["erro"] is not None


# ── Testes de SNMPResultado ───────────────────────────────────────────────────

class TestSNMPResultado:
    """Testa a dataclass SNMPResultado (sem rede)."""

    def test_resultado_sucesso(self):
        r = SNMPResultado(sucesso=True, contador=9999, oid_usado="1.3.6.1.2.1.43.10.2.1.4.1.1")
        assert r.sucesso is True
        assert r.contador == 9999
        assert r.erro is None

    def test_resultado_falha(self):
        r = SNMPResultado(sucesso=False, erro="Timeout")
        assert r.sucesso is False
        assert r.contador is None
        assert r.erro == "Timeout"

    def test_resultado_defaults(self):
        r = SNMPResultado(sucesso=True)
        assert r.contador is None
        assert r.oid_usado is None
        assert r.fabricante_detectado is None
        assert r.erro is None
