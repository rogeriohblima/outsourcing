"""
tests/test_leituras.py — Testes unitários do CRUD de Leituras.

Mudanças em relação à versão anterior:
  - Leitura agora exige contrato_id (vinculada ao contrato para cálculo de franquia)
  - TipoImpressao não tem mais campos de franquia (apenas descricao)
  - Usado contrato_base fixture para prover contrato_id válido

Cobre:
  - Criação de leitura manual com contrato_id
  - Criação via SNMP (mock) com contrato_id
  - Falha SNMP: impressora sem IP
  - Falha SNMP: serviço retorna erro
  - Filtros por contrato, impressora, mês/ano
  - Atualização de contador
  - Remoção
"""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.models import Contrato, Impressora, TipoImpressao
from app.services.snmp_service import SNMPResultado


def _payload_base(impressora: Impressora, tipo: TipoImpressao,
                  contrato: Contrato, mes: int, ano: int,
                  contador: int = 1000) -> dict:
    """Monta payload padrão de leitura para evitar repetição nos testes."""
    return {
        "contrato_id":           contrato.id,
        "impressora_num_serie":  impressora.num_serie,
        "tipo_impressao_id":     tipo.id,
        "contador":              contador,
        "data":                  str(date.today()),
        "mes_referencia":        mes,
        "ano_referencia":        ano,
    }


@pytest.mark.asyncio
class TestLeiturasManual:
    """Testes de leituras inseridas manualmente."""

    async def test_criar_leitura_manual_sucesso(
        self, client: AsyncClient, auth_headers: dict,
        impressora_fixture: Impressora, tipo_impressao: TipoImpressao,
        contrato_base: Contrato,
    ):
        """Criação manual com dados válidos deve retornar HTTP 201."""
        payload = {
            **_payload_base(impressora_fixture, tipo_impressao, contrato_base, 1, 2025, 12345),
            "observacao": "Lançamento manual — SNMP indisponível",
        }
        resp = await client.post("/api/v1/leituras/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["contador"] == 12345
        assert data["manual"] is True
        assert data["contrato_id"] == contrato_base.id
        assert data["impressora"]["num_serie"] == impressora_fixture.num_serie

    async def test_criar_leitura_impressora_inexistente_retorna_404(
        self, client: AsyncClient, auth_headers: dict,
        tipo_impressao: TipoImpressao, contrato_base: Contrato,
    ):
        """Leitura para impressora inexistente deve retornar 404."""
        payload = {
            "contrato_id":          contrato_base.id,
            "impressora_num_serie": "SERIE-NAO-EXISTE",
            "tipo_impressao_id":    tipo_impressao.id,
            "contador":             100,
            "data":                 str(date.today()),
            "mes_referencia":       1,
            "ano_referencia":       2025,
        }
        resp = await client.post("/api/v1/leituras/", json=payload, headers=auth_headers)
        assert resp.status_code == 404

    async def test_filtrar_por_contrato(
        self, client: AsyncClient, auth_headers: dict,
        impressora_fixture: Impressora, tipo_impressao: TipoImpressao,
        contrato_base: Contrato,
    ):
        """Filtro ?contrato_id= deve retornar apenas leituras do contrato."""
        await client.post(
            "/api/v1/leituras/",
            json=_payload_base(impressora_fixture, tipo_impressao, contrato_base, 1, 2025, 500),
            headers=auth_headers,
        )
        resp = await client.get(
            f"/api/v1/leituras/?contrato_id={contrato_base.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        for l in resp.json():
            assert l["contrato_id"] == contrato_base.id

    async def test_filtrar_por_mes(
        self, client: AsyncClient, auth_headers: dict,
        impressora_fixture: Impressora, tipo_impressao: TipoImpressao,
        contrato_base: Contrato,
    ):
        """Filtro por mês/ano deve retornar apenas leituras do período."""
        await client.post(
            "/api/v1/leituras/",
            json=_payload_base(impressora_fixture, tipo_impressao, contrato_base, 1, 2025, 1000),
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/leituras/",
            json=_payload_base(impressora_fixture, tipo_impressao, contrato_base, 2, 2025, 2000),
            headers=auth_headers,
        )
        resp = await client.get(
            "/api/v1/leituras/?mes_referencia=1&ano_referencia=2025",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        for l in resp.json():
            assert l["mes_referencia"] == 1
            assert l["ano_referencia"] == 2025

    async def test_listar_leituras_por_impressora(
        self, client: AsyncClient, auth_headers: dict,
        impressora_fixture: Impressora, tipo_impressao: TipoImpressao,
        contrato_base: Contrato,
    ):
        """Endpoint /leituras/impressora/{num_serie} deve filtrar por impressora."""
        await client.post(
            "/api/v1/leituras/",
            json=_payload_base(impressora_fixture, tipo_impressao, contrato_base, 3, 2025, 500),
            headers=auth_headers,
        )
        resp = await client.get(
            f"/api/v1/leituras/impressora/{impressora_fixture.num_serie}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        for l in resp.json():
            assert l["impressora"]["num_serie"] == impressora_fixture.num_serie

    async def test_atualizar_contador_leitura(
        self, client: AsyncClient, auth_headers: dict,
        impressora_fixture: Impressora, tipo_impressao: TipoImpressao,
        contrato_base: Contrato,
    ):
        """PATCH deve atualizar o contador de uma leitura existente."""
        create = await client.post(
            "/api/v1/leituras/",
            json=_payload_base(impressora_fixture, tipo_impressao, contrato_base, 4, 2025, 1000),
            headers=auth_headers,
        )
        assert create.status_code == 201
        lid = create.json()["id"]

        resp = await client.patch(
            f"/api/v1/leituras/{lid}",
            json={"contador": 1500, "observacao": "Corrigido"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["contador"] == 1500
        assert resp.json()["observacao"] == "Corrigido"

    async def test_remover_leitura(
        self, client: AsyncClient, auth_headers: dict,
        impressora_fixture: Impressora, tipo_impressao: TipoImpressao,
        contrato_base: Contrato,
    ):
        """DELETE deve remover a leitura e retornar 204."""
        create = await client.post(
            "/api/v1/leituras/",
            json=_payload_base(impressora_fixture, tipo_impressao, contrato_base, 5, 2025, 800),
            headers=auth_headers,
        )
        lid = create.json()["id"]
        del_resp = await client.delete(f"/api/v1/leituras/{lid}", headers=auth_headers)
        assert del_resp.status_code == 204
        get_resp = await client.get(f"/api/v1/leituras/{lid}", headers=auth_headers)
        assert get_resp.status_code == 404


@pytest.mark.asyncio
class TestLeiturasSNMP:
    """Testes de leituras automáticas via SNMP (com mock)."""

    async def test_snmp_sucesso_cria_leitura(
        self, client: AsyncClient, auth_headers: dict,
        impressora_fixture: Impressora, tipo_impressao: TipoImpressao,
        contrato_base: Contrato,
    ):
        """Leitura SNMP bem-sucedida deve criar registro com manual=False."""
        mock_res = SNMPResultado(
            sucesso=True, contador=98765,
            oid_usado="1.3.6.1.2.1.43.10.2.1.4.1.1",
        )
        with patch("app.routers.leituras.ler_contador_snmp", new=AsyncMock(return_value=mock_res)):
            resp = await client.post(
                "/api/v1/leituras/snmp",
                json={
                    "contrato_id":          contrato_base.id,
                    "impressora_num_serie":  impressora_fixture.num_serie,
                    "tipo_impressao_id":     tipo_impressao.id,
                    "mes_referencia":        5,
                    "ano_referencia":        2025,
                },
                headers=auth_headers,
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["contador"] == 98765
        assert data["manual"] is False
        assert "SNMP automático" in data["observacao"]

    async def test_snmp_falha_retorna_422(
        self, client: AsyncClient, auth_headers: dict,
        impressora_fixture: Impressora, tipo_impressao: TipoImpressao,
        contrato_base: Contrato,
    ):
        """Falha SNMP deve retornar 422 com orientação para lançamento manual."""
        mock_res = SNMPResultado(sucesso=False, erro="Timeout: host inacessível")
        with patch("app.routers.leituras.ler_contador_snmp", new=AsyncMock(return_value=mock_res)):
            resp = await client.post(
                "/api/v1/leituras/snmp",
                json={
                    "contrato_id":         contrato_base.id,
                    "impressora_num_serie": impressora_fixture.num_serie,
                    "tipo_impressao_id":    tipo_impressao.id,
                    "mes_referencia":       6,
                    "ano_referencia":       2025,
                },
                headers=auth_headers,
            )
        assert resp.status_code == 422
        assert "manual" in resp.json()["detail"].lower()

    async def test_snmp_impressora_sem_ip_retorna_422(
        self, client: AsyncClient, auth_headers: dict,
        tipo_impressora, local_impressora,
        tipo_impressao: TipoImpressao, contrato_base: Contrato,
    ):
        """Impressora sem IP deve retornar 422 antes de tentar SNMP."""
        await client.post(
            "/api/v1/impressoras/",
            json={
                "num_serie": "SN-SEM-IP-TEST",
                "tipo_id":   tipo_impressora.id,
                "local_id":  local_impressora.id,
                "ip":        None,
            },
            headers=auth_headers,
        )
        resp = await client.post(
            "/api/v1/leituras/snmp",
            json={
                "contrato_id":         contrato_base.id,
                "impressora_num_serie": "SN-SEM-IP-TEST",
                "tipo_impressao_id":    tipo_impressao.id,
                "mes_referencia":       7,
                "ano_referencia":       2025,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422
        assert "IP" in resp.json()["detail"]
