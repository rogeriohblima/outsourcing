"""
tests/test_auth.py — Testes unitários do módulo de autenticação.

Cobre:
  - Geração e decodificação de tokens JWT
  - Endpoint POST /auth/login (sucesso e falha)
  - Endpoint GET /auth/me (autenticado e não autenticado)
  - Proteção de endpoints com token inválido/ausente
"""

import pytest
from httpx import AsyncClient

from app.auth.service import criar_token_acesso, decodificar_token, obter_info_usuario


# ── Testes de serviço JWT (sem HTTP) ─────────────────────────────────────────

class TestJWTService:
    """Testa a geração e decodificação de tokens JWT diretamente."""

    def test_criar_token_retorna_string(self):
        """criar_token_acesso deve retornar uma string não-vazia."""
        token = criar_token_acesso("joao", "João Silva", ["GRP_ADMIN"])
        assert isinstance(token, str)
        assert len(token) > 10

    def test_token_pode_ser_decodificado(self):
        """Um token recém-criado deve ser decodificado com sucesso."""
        token = criar_token_acesso("joao", "João Silva", ["GRP_ADMIN"])
        payload = decodificar_token(token)
        assert payload is not None
        assert payload.sub == "joao"
        assert payload.nome == "João Silva"
        assert "GRP_ADMIN" in payload.grupos

    def test_token_invalido_retorna_none(self):
        """Um token malformado deve retornar None ao decodificar."""
        resultado = decodificar_token("token.invalido.aqui")
        assert resultado is None

    def test_token_com_assinatura_errada_retorna_none(self):
        """Token com assinatura manipulada deve ser rejeitado."""
        token = criar_token_acesso("joao", "João", [])
        token_corrompido = token[:-5] + "XXXXX"
        assert decodificar_token(token_corrompido) is None

    def test_obter_info_usuario_valido(self):
        """obter_info_usuario deve retornar UserInfo para token válido."""
        token = criar_token_acesso("maria", "Maria Souza", ["GRP_FISCAL"])
        info = obter_info_usuario(token)
        assert info is not None
        assert info.username == "maria"
        assert info.nome == "Maria Souza"

    def test_obter_info_usuario_invalido_retorna_none(self):
        """obter_info_usuario deve retornar None para token inválido."""
        assert obter_info_usuario("nao-e-um-jwt") is None


# ── Testes dos endpoints HTTP ─────────────────────────────────────────────────

@pytest.mark.asyncio
class TestLoginEndpoint:
    """Testa o endpoint POST /api/v1/auth/login."""

    async def test_login_credenciais_dev_validas(self, client: AsyncClient):
        """
        Login com credenciais de desenvolvimento deve retornar token JWT.

        Requer APP_ENV != production e usuário 'admin'/'admin123' nos _DEV_USERS.
        """
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_login_credenciais_invalidas_retorna_401(self, client: AsyncClient):
        """Login com senha errada deve retornar HTTP 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "senha-errada"},
        )
        assert response.status_code == 401

    async def test_login_usuario_inexistente_retorna_401(self, client: AsyncClient):
        """Login com usuário inexistente deve retornar HTTP 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "usuario_nao_existe", "password": "qualquer"},
        )
        assert response.status_code == 401

    async def test_login_body_incompleto_retorna_422(self, client: AsyncClient):
        """Request sem campo obrigatório deve retornar HTTP 422."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin"},  # falta password
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestMeEndpoint:
    """Testa o endpoint GET /api/v1/auth/me."""

    async def test_me_autenticado_retorna_dados(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Endpoint /me com token válido deve retornar dados do usuário."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "test_user"
        assert data["nome"] == "Usuário de Teste"

    async def test_me_sem_token_retorna_403(self, client: AsyncClient):
        """Endpoint /me sem header Authorization deve retornar HTTP 403."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)

    async def test_me_token_invalido_retorna_401(self, client: AsyncClient):
        """Endpoint /me com token inválido deve retornar HTTP 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer token.invalido"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestProtecaoEndpoints:
    """Garante que endpoints protegidos rejeitam requisições sem token."""

    async def test_endpoint_protegido_sem_auth_retorna_403(self, client: AsyncClient):
        """GET /membros/ sem token deve ser rejeitado."""
        response = await client.get("/api/v1/membros/")
        assert response.status_code in (401, 403)

    async def test_health_publico_nao_requer_auth(self, client: AsyncClient):
        """GET /health deve estar acessível sem autenticação."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
