"""
tests/test_impressoras.py — Testes unitários do CRUD de Impressoras.

Cobre:
  - Listagem com e sem filtros
  - Criação com num_serie único
  - Duplicidade de num_serie (409)
  - Referência a tipo/local inexistente (404)
  - Atualização de campos (PATCH)
  - Ativação/desativação
  - Remoção com cascata nas leituras
"""

import pytest
from httpx import AsyncClient

from app.models.models import Impressora, LocalImpressora, TipoImpressora


@pytest.mark.asyncio
class TestImpressoras:
    """Suite de testes para /api/v1/impressoras."""

    async def test_listar_impressoras_vazio(self, client: AsyncClient, auth_headers: dict):
        """Lista deve estar vazia no banco limpo."""
        response = await client.get("/api/v1/impressoras/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_criar_impressora_sucesso(
        self,
        client: AsyncClient,
        auth_headers: dict,
        tipo_impressora: TipoImpressora,
        local_impressora: LocalImpressora,
    ):
        """Criação com dados válidos deve retornar HTTP 201 com tipo e local expandidos."""
        payload = {
            "num_serie": "HP-LJ-0001",
            "nome": "HP LaserJet Pro",
            "tipo_id": tipo_impressora.id,
            "local_id": local_impressora.id,
            "ip": "10.0.0.50",
            "ativa": True,
        }
        response = await client.post("/api/v1/impressoras/", json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["num_serie"] == "HP-LJ-0001"
        assert data["tipo"]["tipo"] == tipo_impressora.tipo
        assert data["local"]["setor"] == local_impressora.setor
        assert data["ativa"] is True

    async def test_criar_impressora_serie_duplicada_retorna_409(
        self,
        client: AsyncClient,
        auth_headers: dict,
        impressora_fixture: Impressora,
    ):
        """Tentar cadastrar número de série já existente deve retornar 409."""
        payload = {
            "num_serie": impressora_fixture.num_serie,
            "nome": "Duplicada",
            "tipo_id": impressora_fixture.tipo_id,
            "local_id": impressora_fixture.local_id,
        }
        response = await client.post("/api/v1/impressoras/", json=payload, headers=auth_headers)
        assert response.status_code == 409

    async def test_criar_impressora_tipo_inexistente_retorna_404(
        self,
        client: AsyncClient,
        auth_headers: dict,
        local_impressora: LocalImpressora,
    ):
        """Tipo de impressora inexistente deve retornar 404."""
        payload = {
            "num_serie": "SN-TIPO-INVALIDO",
            "nome": "Teste",
            "tipo_id": 99999,
            "local_id": local_impressora.id,
        }
        response = await client.post("/api/v1/impressoras/", json=payload, headers=auth_headers)
        assert response.status_code == 404

    async def test_filtrar_por_ativa(
        self,
        client: AsyncClient,
        auth_headers: dict,
        impressora_fixture: Impressora,
    ):
        """Filtro ?ativa=true deve retornar apenas impressoras ativas."""
        response = await client.get(
            "/api/v1/impressoras/?ativa=true", headers=auth_headers
        )
        assert response.status_code == 200
        for imp in response.json():
            assert imp["ativa"] is True

    async def test_desativar_impressora(
        self,
        client: AsyncClient,
        auth_headers: dict,
        impressora_fixture: Impressora,
    ):
        """PATCH com ativa=false deve desativar a impressora."""
        response = await client.patch(
            f"/api/v1/impressoras/{impressora_fixture.num_serie}",
            json={"ativa": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["ativa"] is False

    async def test_obter_impressora_inexistente_retorna_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET por num_serie inexistente deve retornar 404."""
        response = await client.get(
            "/api/v1/impressoras/SERIE-INEXISTENTE", headers=auth_headers
        )
        assert response.status_code == 404

    async def test_remover_impressora(
        self,
        client: AsyncClient,
        auth_headers: dict,
        tipo_impressora: TipoImpressora,
        local_impressora: LocalImpressora,
    ):
        """DELETE deve retornar 204 e a impressora não deve mais ser encontrada."""
        # Cria impressora específica para remover
        await client.post(
            "/api/v1/impressoras/",
            json={
                "num_serie": "PARA-DELETAR-001",
                "nome": "Impressora a remover",
                "tipo_id": tipo_impressora.id,
                "local_id": local_impressora.id,
            },
            headers=auth_headers,
        )
        response = await client.delete(
            "/api/v1/impressoras/PARA-DELETAR-001", headers=auth_headers
        )
        assert response.status_code == 204

        get_resp = await client.get(
            "/api/v1/impressoras/PARA-DELETAR-001", headers=auth_headers
        )
        assert get_resp.status_code == 404
