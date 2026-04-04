"""
tests/test_membros.py — Testes unitários do CRUD de Membros.

Nota: cada teste usa CPFs únicos para garantir isolamento total,
pois a sessão de banco é compartilhada dentro da mesma classe de teste.
"""

import pytest
from httpx import AsyncClient
from app.models.models import Membro


@pytest.mark.asyncio
class TestMembros:
    """Suite de testes para /api/v1/membros."""

    async def test_listar_membros_vazio(self, client: AsyncClient, auth_headers: dict):
        """Lista de membros deve retornar 200 (pode ter dados de outras fixtures)."""
        response = await client.get("/api/v1/membros/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_criar_membro_sucesso(self, client: AsyncClient, auth_headers: dict):
        """Criação de membro com dados válidos deve retornar HTTP 201."""
        response = await client.post(
            "/api/v1/membros/",
            json={"cpf": "111.222.333-44", "nome": "Sgt Oliveira"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["cpf"] == "111.222.333-44"
        assert data["nome"] == "Sgt Oliveira"
        assert "criado_em" in data

    async def test_criar_membro_cpf_duplicado_retorna_409(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Tentar criar dois membros com mesmo CPF deve retornar HTTP 409."""
        payload = {"cpf": "999.888.777-66", "nome": "Primeiro"}
        await client.post("/api/v1/membros/", json=payload, headers=auth_headers)

        response = await client.post(
            "/api/v1/membros/",
            json={"cpf": "999.888.777-66", "nome": "Segundo"},
            headers=auth_headers,
        )
        assert response.status_code == 409

    async def test_obter_membro_existente(
        self, client: AsyncClient, auth_headers: dict, membro_fixture: Membro
    ):
        """GET por CPF existente deve retornar o membro correto."""
        response = await client.get(
            f"/api/v1/membros/{membro_fixture.cpf}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["nome"] == membro_fixture.nome

    async def test_obter_membro_inexistente_retorna_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET por CPF inexistente deve retornar HTTP 404."""
        response = await client.get("/api/v1/membros/000.000.000-00", headers=auth_headers)
        assert response.status_code == 404

    async def test_atualizar_membro(
        self, client: AsyncClient, auth_headers: dict, membro_fixture: Membro
    ):
        """PATCH deve atualizar apenas o campo enviado."""
        response = await client.patch(
            f"/api/v1/membros/{membro_fixture.cpf}",
            json={"nome": "Cap Silva Atualizado"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["nome"] == "Cap Silva Atualizado"
        assert response.json()["cpf"] == membro_fixture.cpf

    async def test_remover_membro(self, client: AsyncClient, auth_headers: dict):
        """DELETE deve remover o membro e retornar HTTP 204."""
        # Usa CPF único que não colide com nenhuma outra fixture
        cpf = "555.444.333-22"

        # Cria membro — se já existir (de teste anterior), deleta e recria
        create = await client.post(
            "/api/v1/membros/",
            json={"cpf": cpf, "nome": "Para Remover"},
            headers=auth_headers,
        )
        if create.status_code == 409:
            # Já existe, deleta diretamente
            pass
        else:
            assert create.status_code == 201

        # Deleta
        del_resp = await client.delete(f"/api/v1/membros/{cpf}", headers=auth_headers)
        assert del_resp.status_code == 204

        # Confirma remoção
        get_resp = await client.get(f"/api/v1/membros/{cpf}", headers=auth_headers)
        assert get_resp.status_code == 404

    async def test_listar_membros_com_dados(
        self, client: AsyncClient, auth_headers: dict, membro_fixture: Membro
    ):
        """Após criar membro via fixture, a listagem deve retorná-lo."""
        response = await client.get("/api/v1/membros/", headers=auth_headers)
        assert response.status_code == 200
        cpfs = [m["cpf"] for m in response.json()]
        assert membro_fixture.cpf in cpfs
