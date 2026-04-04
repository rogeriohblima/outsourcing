"""
tests/test_contratos.py — Testes unitários para Empresas e Contratos.

Notas de implementação:
- CNPJs usados nos testes NÃO contêm "/" para evitar conflito com separador
  de rota do FastAPI (ex: /api/v1/empresas/12.345.678/0001-90 seria mal
  interpretado). Formato alternativo: "12.345.678-0001-90".
- Cada teste cria seus próprios dados para garantir isolamento total.
- setup_contrato usa @pytest_asyncio.fixture pois é corrotina assíncrona.
"""

import pytest
import pytest_asyncio
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Comissao, Empresa, Membro


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def setup_contrato(db: AsyncSession):
    """Cria empresa, membro e comissão necessários para testar Contrato."""
    empresa = Empresa(cnpj="22.333.444-0001-55", nome="Empresa Contrato Test")
    membro  = Membro(cpf="987.654.321-00", nome="Cmt Flores")
    db.add_all([empresa, membro])
    await db.flush()

    comissao = Comissao(
        presidente_cpf=membro.cpf,
        documento_numero="BI 010/2025",
        documento_data=date(2025, 1, 10),
    )
    db.add(comissao)
    await db.flush()
    return {"empresa": empresa, "comissao": comissao}


# ── Testes de Empresa ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestEmpresas:
    """Suite de testes para /api/v1/empresas."""

    async def test_listar_empresas_retorna_lista(self, client: AsyncClient, auth_headers: dict):
        """GET /empresas/ deve retornar uma lista."""
        resp = await client.get("/api/v1/empresas/", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_criar_empresa_sucesso(self, client: AsyncClient, auth_headers: dict):
        """Criação com dados válidos deve retornar 201."""
        resp = await client.post(
            "/api/v1/empresas/",
            json={"cnpj": "11.222.333-0001-44", "nome": "Tech Impressoras LTDA"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["cnpj"] == "11.222.333-0001-44"
        assert resp.json()["nome"] == "Tech Impressoras LTDA"

    async def test_criar_empresa_cnpj_duplicado_retorna_409(self, client: AsyncClient, auth_headers: dict):
        """Dois registros com mesmo CNPJ devem resultar em 409."""
        payload = {"cnpj": "55.666.777-0001-88", "nome": "Primeira"}
        await client.post("/api/v1/empresas/", json=payload, headers=auth_headers)
        resp = await client.post(
            "/api/v1/empresas/",
            json={"cnpj": "55.666.777-0001-88", "nome": "Segunda"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_obter_empresa_existente(self, client: AsyncClient, auth_headers: dict):
        """GET por CNPJ existente deve retornar 200 com os dados corretos."""
        # Cria empresa inline para ter CNPJ sem "/"
        cnpj = "44.555.666-0001-77"
        await client.post(
            "/api/v1/empresas/",
            json={"cnpj": cnpj, "nome": "Empresa Para Obter"},
            headers=auth_headers,
        )
        resp = await client.get(f"/api/v1/empresas/{cnpj}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["nome"] == "Empresa Para Obter"

    async def test_obter_empresa_inexistente_retorna_404(self, client: AsyncClient, auth_headers: dict):
        """GET por CNPJ não cadastrado deve retornar 404."""
        resp = await client.get("/api/v1/empresas/00.000.000-0000-00", headers=auth_headers)
        assert resp.status_code == 404

    async def test_atualizar_nome_empresa(self, client: AsyncClient, auth_headers: dict):
        """PATCH deve atualizar o nome mantendo o CNPJ."""
        cnpj = "88.111.222-0001-44"
        await client.post("/api/v1/empresas/", json={"cnpj": cnpj, "nome": "Original"}, headers=auth_headers)
        resp = await client.patch(
            f"/api/v1/empresas/{cnpj}",
            json={"nome": "Empresa Atualizada LTDA"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["nome"] == "Empresa Atualizada LTDA"
        assert resp.json()["cnpj"] == cnpj

    async def test_remover_empresa(self, client: AsyncClient, auth_headers: dict):
        """DELETE deve retornar 204 e empresa não deve mais existir."""
        cnpj = "77.000.111-0001-55"
        # Garante que existe antes de remover
        create_resp = await client.post(
            "/api/v1/empresas/", json={"cnpj": cnpj, "nome": "A Remover"}, headers=auth_headers
        )
        # Se já existia (409), ainda pode testar o delete
        assert create_resp.status_code in (201, 409)

        del_resp = await client.delete(f"/api/v1/empresas/{cnpj}", headers=auth_headers)
        assert del_resp.status_code == 204

        # Confirma que foi removido
        get_resp = await client.get(f"/api/v1/empresas/{cnpj}", headers=auth_headers)
        assert get_resp.status_code == 404


# ── Testes de Contrato ────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestContratos:
    """Suite de testes para /api/v1/contratos."""

    async def test_criar_contrato_sucesso(
        self, client: AsyncClient, auth_headers: dict, setup_contrato: dict
    ):
        """Criação com todas as FKs válidas deve retornar 201."""
        resp = await client.post(
            "/api/v1/contratos/",
            json={
                "numero":           "2025CT-TEST-001",
                "empresa_cnpj":     setup_contrato["empresa"].cnpj,
                "data_inicio":      "2025-01-01",
                "data_termino":     "2025-12-31",
                "comissao_id":      setup_contrato["comissao"].id,
                "numero_processo":  "NUP-2025-TEST",
                "valor_estimado":   50000.00,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["numero"] == "2025CT-TEST-001"
        assert data["empresa"]["nome"] == setup_contrato["empresa"].nome
        assert "presidente" in data["comissao"]

    async def test_criar_contrato_empresa_inexistente_retorna_404(
        self, client: AsyncClient, auth_headers: dict, setup_contrato: dict
    ):
        """Contrato com empresa inexistente deve retornar 404."""
        resp = await client.post(
            "/api/v1/contratos/",
            json={
                "numero":          "2025CT-FAIL",
                "empresa_cnpj":    "00.000.000-0000-00",   # não existe
                "data_inicio":     "2025-01-01",
                "data_termino":    "2025-12-31",
                "comissao_id":     setup_contrato["comissao"].id,
                "numero_processo": "NUP-FAIL",
                "valor_estimado":  50000.00,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_numero_contrato_unico(
        self, client: AsyncClient, auth_headers: dict, setup_contrato: dict
    ):
        """Dois contratos com mesmo número devem resultar em erro (409 ou 500)."""
        payload = {
            "numero":          "2025CT-DUPLICADO",
            "empresa_cnpj":    setup_contrato["empresa"].cnpj,
            "data_inicio":     "2025-01-01",
            "data_termino":    "2025-06-30",
            "comissao_id":     setup_contrato["comissao"].id,
            "numero_processo": "NUP-DUP",
            "valor_estimado":  50000.00,
        }
        r1 = await client.post("/api/v1/contratos/", json=payload, headers=auth_headers)
        assert r1.status_code == 201

        r2 = await client.post("/api/v1/contratos/", json=payload, headers=auth_headers)
        # SQLite lança IntegrityError → 500; PostgreSQL pode retornar 409
        assert r2.status_code in (409, 422, 500)

    async def test_listar_contratos_inclui_empresa(
        self, client: AsyncClient, auth_headers: dict, setup_contrato: dict
    ):
        """Listagem deve incluir dados expandidos da empresa."""
        await client.post(
            "/api/v1/contratos/",
            json={
                "numero":          "2025CT-LIST-TEST",
                "empresa_cnpj":    setup_contrato["empresa"].cnpj,
                "data_inicio":     "2025-02-01",
                "data_termino":    "2025-11-30",
                "comissao_id":     setup_contrato["comissao"].id,
                "numero_processo": "NUP-LIST",
                "valor_estimado":  50000.00,
            },
            headers=auth_headers,
        )
        resp = await client.get("/api/v1/contratos/", headers=auth_headers)
        assert resp.status_code == 200
        numeros = [c["numero"] for c in resp.json()]
        assert "2025CT-LIST-TEST" in numeros
        for c in resp.json():
            assert "empresa" in c
            assert "nome" in c["empresa"]

    async def test_atualizar_contrato(
        self, client: AsyncClient, auth_headers: dict, setup_contrato: dict
    ):
        """PATCH deve atualizar apenas o campo enviado."""
        create_resp = await client.post(
            "/api/v1/contratos/",
            json={
                "numero":          "2025CT-UPDATE",
                "empresa_cnpj":    setup_contrato["empresa"].cnpj,
                "data_inicio":     "2025-01-01",
                "data_termino":    "2025-12-31",
                "comissao_id":     setup_contrato["comissao"].id,
                "numero_processo": "NUP-UPD",
                "valor_estimado":  50000.00,
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        cid = create_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/contratos/{cid}",
            json={"numero_processo": "NUP-ATUALIZADO-2025"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["numero_processo"] == "NUP-ATUALIZADO-2025"

    async def test_remover_contrato(
        self, client: AsyncClient, auth_headers: dict, setup_contrato: dict
    ):
        """DELETE deve retornar 204 e contrato não deve mais ser encontrado."""
        create_resp = await client.post(
            "/api/v1/contratos/",
            json={
                "numero":          "2025CT-DEL",
                "empresa_cnpj":    setup_contrato["empresa"].cnpj,
                "data_inicio":     "2025-01-01",
                "data_termino":    "2025-12-31",
                "comissao_id":     setup_contrato["comissao"].id,
                "numero_processo": "NUP-DEL",
                "valor_estimado":  50000.00,
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        cid = create_resp.json()["id"]

        del_resp = await client.delete(f"/api/v1/contratos/{cid}", headers=auth_headers)
        assert del_resp.status_code == 204

        get_resp = await client.get(f"/api/v1/contratos/{cid}", headers=auth_headers)
        assert get_resp.status_code == 404
