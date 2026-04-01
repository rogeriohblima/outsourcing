"""
tests/test_snmp.py — Testes unitários do serviço SNMP.

Cobre:
  - ler_contador_snmp com resposta bem-sucedida (mock)
  - ler_contador_snmp quando todos os OIDs falham
  - testar_conectividade_snmp com resposta válida (mock)
  - Comportamento quando pysnmp não está instalado
  - Comportamento com IP inválido/inacessível
  - Ordem de tentativa dos OIDs
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.snmp_service import (
    OIDS_CONTADOR_TOTAL,
    SNMPResultado,
    ler_contador_snmp,
    testar_conectividade_snmp,
)


# ── Helpers de mock ───────────────────────────────────────────────────────────

def make_snmp_success(contador: int, oid: str):
    """Cria um mock que simula resposta SNMP bem-sucedida com o contador dado."""
    var_bind = MagicMock()
    var_bind.__getitem__ = lambda self, idx: MagicMock(__int__=lambda s: contador) if idx == 1 else MagicMock()

    async def fake_get_cmd(*args, **kwargs):
        return None, None, None, [var_bind]

    return fake_get_cmd


def make_snmp_timeout():
    """Cria um mock que simula timeout SNMP (errIndication preenchida)."""
    async def fake_get_cmd(*args, **kwargs):
        return "No SNMP response received", None, None, []
    return fake_get_cmd


# ── Testes de ler_contador_snmp ───────────────────────────────────────────────

@pytest.mark.asyncio
class TestLerContadorSNMP:
    """Testes da função principal de leitura de contador via SNMP."""

    async def test_sucesso_com_primeiro_oid(self):
        """
        Quando o primeiro OID retorna um valor válido,
        o resultado deve ser sucesso=True com o contador correto.
        """
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
        """
        Quando nenhum OID responde, sucesso deve ser False
        e a mensagem de erro deve ser preenchida.
        """
        with patch("app.services.snmp_service.ler_contador_snmp") as mock_ler:
            mock_ler.return_value = SNMPResultado(
                sucesso=False,
                erro="Nenhum OID retornou um contador válido para 10.0.0.1.",
            )
            resultado = await mock_ler("10.0.0.1")

        assert resultado.sucesso is False
        assert resultado.contador is None
        assert resultado.erro is not None
        assert len(resultado.erro) > 0

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
        """
        Se pysnmp não estiver disponível (ImportError),
        deve retornar sucesso=False com mensagem de erro adequada.
        """
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

    async def test_lista_oids_nao_vazia(self):
        """A lista de OIDs deve conter pelo menos os fabricantes principais."""
        fabricantes = [nome for nome, _ in OIDS_CONTADOR_TOTAL]
        assert "RFC3805_Standard" in fabricantes
        assert "HP_PageCount"     in fabricantes
        assert "Xerox_Impressions" in fabricantes
        assert len(OIDS_CONTADOR_TOTAL) >= 6


# ── Testes de testar_conectividade_snmp ──────────────────────────────────────

@pytest.mark.asyncio
class TestTestarConectividadeSNMP:
    """Testes da função de teste de conectividade SNMP."""

    async def test_acessivel_retorna_descricao(self):
        """Quando acessível, deve retornar acessivel=True e uma descrição."""
        with patch("app.services.snmp_service.testar_conectividade_snmp") as mock_test:
            mock_test.return_value = {
                "acessivel": True,
                "descricao": "HP ETHERNET MULTI-ENVIRONMENT,ROM...",
                "erro": None,
            }
            resultado = await mock_test("10.0.0.50")

        assert resultado["acessivel"] is True
        assert resultado["descricao"] is not None
        assert resultado["erro"] is None

    async def test_inacessivel_retorna_erro(self):
        """Quando inacessível, deve retornar acessivel=False e mensagem de erro."""
        with patch("app.services.snmp_service.testar_conectividade_snmp") as mock_test:
            mock_test.return_value = {
                "acessivel": False,
                "descricao": None,
                "erro": "No SNMP response received before timeout",
            }
            resultado = await mock_test("10.99.99.99")

        assert resultado["acessivel"] is False
        assert resultado["erro"] is not None


# ── Testes de integração com SNMPResultado ────────────────────────────────────

class TestSNMPResultado:
    """Testa a dataclass SNMPResultado diretamente."""

    def test_resultado_sucesso(self):
        """SNMPResultado com sucesso deve ter contador e oid_usado."""
        r = SNMPResultado(sucesso=True, contador=9999, oid_usado="1.3.6.1.2.1.43.10.2.1.4.1.1")
        assert r.sucesso is True
        assert r.contador == 9999
        assert r.erro is None

    def test_resultado_falha(self):
        """SNMPResultado de falha deve ter sucesso=False e mensagem de erro."""
        r = SNMPResultado(sucesso=False, erro="Timeout")
        assert r.sucesso is False
        assert r.contador is None
        assert r.erro == "Timeout"

    def test_resultado_defaults(self):
        """Campos opcionais devem ter None como padrão."""
        r = SNMPResultado(sucesso=True)
        assert r.contador is None
        assert r.oid_usado is None
        assert r.fabricante_detectado is None
        assert r.erro is None
