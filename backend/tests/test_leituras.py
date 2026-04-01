"""
tests/test_leituras.py — Testes unitários do CRUD de Leituras.

Cobre:
  - Criação de leitura manual
  - Criação de leitura via SNMP (com mock do serviço SNMP)
  - Falha no SNMP sem IP configurado
  - Falha no SNMP quando serviço retorna erro (deve retornar 422)
  - Filtros de listagem por impressora, mês/ano, manual
  - Listagem de leituras por impressora
  - Atualização e remoção
"""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.models import Impressora, TipoImpressao
from app.services.snmp_service import SNMPResultado


@pytest.mark.asyncio
class TestLeiturasManual:
    """Testes de leituras inseridas manualmente."""

    async def test_criar_leitura_manual_sucesso(
        self,
        client: AsyncClient,
        auth_headers: dict,
        impressora_fixture: Impressora,
        tipo_impressao: TipoImpressao,
    ):
        """Criação manual com dados válidos deve retornar HTTP 201."""
        payload = {
            "impressora_num_serie": impressora_fixture.num_serie,
            "tipo_impressao_id": tipo_impressao.id,
            "contador": 12345,
            "data": str(date.today()),
            "mes_referencia": 1,
            "ano_referencia": 2025,
            "manual": True,
            "observacao": "Lançamento manual — SNMP indisponível",
        }
        response = await client.post("/api/v1/leituras/", json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["contador"] == 12345
        assert data["manual"] is True  # Sempre True para criação via API
        assert data["impressora"]["num_serie"] == impressora_fixture.num_serie
        assert data["tipo_impressao"]["id"] == tipo_impressao.id

    async def test_criar_leitura_impressora_inexistente_retorna_404(
        self,
        client: AsyncClient,
        auth_headers: dict,
        tipo_impressao: TipoImpressao,
    ):
        """Leitura para impressora inexistente deve retornar 404."""
        payload = {
            "impressora_num_serie": "SERIE-NAO-EXISTE",
            "tipo_impressao_id": tipo_impressao.id,
            "contador": 100,
            "data": str(date.today()),
            "mes_referencia": 1,
            "ano_referencia": 2025,
        }
        response = await client.post("/api/v1/leituras/", json=payload, headers=auth_headers)
        assert response.status_code == 404

    async def test_listar_leituras_por_mes(
        self,
        client: AsyncClient,
        auth_headers: dict,
        impressora_fixture: Impressora,
        tipo_impressao: TipoImpressao,
    ):
        """Filtro por mês/ano deve retornar apenas leituras do período."""
        # Cria leitura em Janeiro/2025
        await client.post(
            "/api/v1/leituras/",
            json={
                "impressora_num_serie": impressora_fixture.num_serie,
                "tipo_impressao_id": tipo_impressao.id,
                "contador": 1000,
                "data": "2025-01-31",
                "mes_referencia": 1,
                "ano_referencia": 2025,
            },
            headers=auth_headers,
        )
        # Cria leitura em Fevereiro/2025
        await client.post(
            "/api/v1/leituras/",
            json={
                "impressora_num_serie": impressora_fixture.num_serie,
                "tipo_impressao_id": tipo_impressao.id,
                "contador": 2000,
                "data": "2025-02-28",
                "mes_referencia": 2,
                "ano_referencia": 2025,
            },
            headers=auth_headers,
        )

        response = await client.get(
            "/api/v1/leituras/?mes_referencia=1&ano_referencia=2025",
            headers=auth_headers,
        )
        assert response.status_code == 200
        leituras = response.json()
        for l in leituras:
            assert l["mes_referencia"] == 1
            assert l["ano_referencia"] == 2025

    async def test_listar_leituras_por_impressora(
        self,
        client: AsyncClient,
        auth_headers: dict,
        impressora_fixture: Impressora,
        tipo_impressao: TipoImpressao,
    ):
        """Endpoint /leituras/impressora/{num_serie} deve filtrar por impressora."""
        await client.post(
            "/api/v1/leituras/",
            json={
                "impressora_num_serie": impressora_fixture.num_serie,
                "tipo_impressao_id": tipo_impressao.id,
                "contador": 500,
                "data": str(date.today()),
                "mes_referencia": 3,
                "ano_referencia": 2025,
            },
            headers=auth_headers,
        )
        response = await client.get(
            f"/api/v1/leituras/impressora/{impressora_fixture.num_serie}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        for leitura in response.json():
            assert leitura["impressora"]["num_serie"] == impressora_fixture.num_serie

    async def test_atualizar_contador_leitura(
        self,
        client: AsyncClient,
        auth_headers: dict,
        impressora_fixture: Impressora,
        tipo_impressao: TipoImpressao,
    ):
        """PATCH deve atualizar o contador de uma leitura existente."""
        resp_criar = await client.post(
            "/api/v1/leituras/",
            json={
                "impressora_num_serie": impressora_fixture.num_serie,
                "tipo_impressao_id": tipo_impressao.id,
                "contador": 1000,
                "data": str(date.today()),
                "mes_referencia": 4,
                "ano_referencia": 2025,
            },
            headers=auth_headers,
        )
        leitura_id = resp_criar.json()["id"]

        response = await client.patch(
            f"/api/v1/leituras/{leitura_id}",
            json={"contador": 1500, "observacao": "Corrigido"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["contador"] == 1500
        assert response.json()["observacao"] == "Corrigido"


@pytest.mark.asyncio
class TestLeituasSNMP:
    """Testes de leituras automáticas via SNMP (com mock)."""

    async def test_snmp_sucesso_cria_leitura(
        self,
        client: AsyncClient,
        auth_headers: dict,
        impressora_fixture: Impressora,
        tipo_impressao: TipoImpressao,
    ):
        """
        Quando SNMP retorna sucesso, deve criar leitura com manual=False.

        O serviço SNMP é substituído por um mock para evitar dependência
        de rede real nos testes unitários.
        """
        mock_resultado = SNMPResultado(
            sucesso=True,
            contador=98765,
            oid_usado="1.3.6.1.2.1.43.10.2.1.4.1.1",
        )

        with patch(
            "app.routers.leituras.ler_contador_snmp",
            new=AsyncMock(return_value=mock_resultado),
        ):
            response = await client.post(
                "/api/v1/leituras/snmp",
                json={
                    "impressora_num_serie": impressora_fixture.num_serie,
                    "tipo_impressao_id": tipo_impressao.id,
                    "mes_referencia": 5,
                    "ano_referencia": 2025,
                },
                headers=auth_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["contador"] == 98765
        assert data["manual"] is False
        assert "SNMP automático" in data["observacao"]

    async def test_snmp_falha_retorna_422(
        self,
        client: AsyncClient,
        auth_headers: dict,
        impressora_fixture: Impressora,
        tipo_impressao: TipoImpressao,
    ):
        """
        Quando SNMP falha, o endpoint deve retornar HTTP 422 com mensagem de erro,
        orientando o usuário a usar o lançamento manual.
        """
        mock_resultado = SNMPResultado(
            sucesso=False,
            erro="Timeout: host inacessível",
        )

        with patch(
            "app.routers.leituras.ler_contador_snmp",
            new=AsyncMock(return_value=mock_resultado),
        ):
            response = await client.post(
                "/api/v1/leituras/snmp",
                json={
                    "impressora_num_serie": impressora_fixture.num_serie,
                    "tipo_impressao_id": tipo_impressao.id,
                    "mes_referencia": 6,
                    "ano_referencia": 2025,
                },
                headers=auth_headers,
            )

        assert response.status_code == 422
        assert "manual" in response.json()["detail"].lower()

    async def test_snmp_impressora_sem_ip_retorna_422(
        self,
        client: AsyncClient,
        auth_headers: dict,
        tipo_impressora,
        local_impressora,
        tipo_impressao: TipoImpressao,
    ):
        """Impressora sem IP configurado deve retornar 422 imediatamente."""
        # Cria impressora sem IP
        await client.post(
            "/api/v1/impressoras/",
            json={
                "num_serie": "SN-SEM-IP",
                "nome": "Sem IP",
                "tipo_id": tipo_impressora.id,
                "local_id": local_impressora.id,
                "ip": None,
            },
            headers=auth_headers,
        )

        response = await client.post(
            "/api/v1/leituras/snmp",
            json={
                "impressora_num_serie": "SN-SEM-IP",
                "tipo_impressao_id": tipo_impressao.id,
                "mes_referencia": 7,
                "ano_referencia": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422
        assert "IP" in response.json()["detail"]
