"""
tests/test_membros.py — Testes unitários do CRUD de Membros.

Cobre:
  - Listagem de membros
  - Criação com CPF válido
  - Duplicidade de CPF (deve retornar 409)
  - Busca por CPF existente e inexistente
  - Atualização parcial (PATCH)
  - Remoção
"""

import pytest
from httpx import AsyncClient

from app.models.models import Membro


@pytest.mark.asyncio
class TestMembros:
    """Suite de testes para o endpoint /api/v1/membros."""

    async def test_listar_membros_vazio(self, client: AsyncClient, auth_headers: dict):
        """Lista de membros deve começar vazia num banco limpo."""
        response = await client.get("/api/v1/membros/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

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
        # CPF não deve mudar
        assert response.json()["cpf"] == membro_fixture.cpf

    async def test_remover_membro(
        self, client: AsyncClient, auth_headers: dict
    ):
        """DELETE deve remover o membro e retornar HTTP 204."""
        # Cria membro para depois remover
        await client.post(
            "/api/v1/membros/",
            json={"cpf": "555.444.333-22", "nome": "Para Remover"},
            headers=auth_headers,
        )
        response = await client.delete(
            "/api/v1/membros/555.444.333-22", headers=auth_headers
        )
        assert response.status_code == 204

        # Confirma que foi removido
        get_response = await client.get(
            "/api/v1/membros/555.444.333-22", headers=auth_headers
        )
        assert get_response.status_code == 404

    async def test_listar_membros_com_dados(
        self, client: AsyncClient, auth_headers: dict, membro_fixture: Membro
    ):
        """Após criar membro, a listagem deve retorná-lo."""
        response = await client.get("/api/v1/membros/", headers=auth_headers)
        assert response.status_code == 200
        cpfs = [m["cpf"] for m in response.json()]
        assert membro_fixture.cpf in cpfs
