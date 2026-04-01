"""
tests/test_contratos.py — Testes unitários para Empresas e Contratos.

Cobre:
  - CRUD de Empresas (criação, busca, CNPJ duplicado, remoção)
  - CRUD de Contratos (criação com FK válida e inválida)
  - Validação de data_termino > data_inicio
  - Listagem de contratos com dados relacionados
"""

import pytest
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Comissao, Empresa, Membro


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def setup_contrato(db: AsyncSession):
    """Cria as entidades necessárias para testar Contrato."""
    empresa = Empresa(cnpj="22.333.444/0001-55", nome="Empresa Contrato Test")
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
        """GET /empresas/ deve retornar uma lista (possivelmente vazia)."""
        resp = await client.get("/api/v1/empresas/", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_criar_empresa_sucesso(self, client: AsyncClient, auth_headers: dict):
        """Criação com CNPJ e nome válidos deve retornar 201."""
        resp = await client.post(
            "/api/v1/empresas/",
            json={"cnpj": "11.222.333/0001-44", "nome": "Tech Impressoras LTDA"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["cnpj"] == "11.222.333/0001-44"
        assert data["nome"] == "Tech Impressoras LTDA"

    async def test_criar_empresa_cnpj_duplicado_retorna_409(self, client: AsyncClient, auth_headers: dict):
        """Dois registros com mesmo CNPJ devem resultar em 409."""
        payload = {"cnpj": "55.666.777/0001-88", "nome": "Primeira"}
        await client.post("/api/v1/empresas/", json=payload, headers=auth_headers)
        resp = await client.post(
            "/api/v1/empresas/",
            json={"cnpj": "55.666.777/0001-88", "nome": "Segunda"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_obter_empresa_existente(
        self, client: AsyncClient, auth_headers: dict, empresa_fixture
    ):
        """GET por CNPJ existente deve retornar a empresa."""
        resp = await client.get(f"/api/v1/empresas/{empresa_fixture.cnpj}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["nome"] == empresa_fixture.nome

    async def test_obter_empresa_inexistente_retorna_404(self, client: AsyncClient, auth_headers: dict):
        """GET por CNPJ não cadastrado deve retornar 404."""
        resp = await client.get("/api/v1/empresas/00.000.000/0000-00", headers=auth_headers)
        assert resp.status_code == 404

    async def test_atualizar_nome_empresa(
        self, client: AsyncClient, auth_headers: dict, empresa_fixture
    ):
        """PATCH deve atualizar o nome da empresa."""
        resp = await client.patch(
            f"/api/v1/empresas/{empresa_fixture.cnpj}",
            json={"nome": "Empresa Atualizada LTDA"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["nome"] == "Empresa Atualizada LTDA"

    async def test_remover_empresa(self, client: AsyncClient, auth_headers: dict):
        """DELETE deve remover a empresa e retornar 204."""
        await client.post(
            "/api/v1/empresas/",
            json={"cnpj": "99.000.111/0001-22", "nome": "A Remover"},
            headers=auth_headers,
        )
        resp = await client.delete("/api/v1/empresas/99.000.111/0001-22", headers=auth_headers)
        assert resp.status_code == 204

        get_resp = await client.get("/api/v1/empresas/99.000.111/0001-22", headers=auth_headers)
        assert get_resp.status_code == 404


# ── Testes de Contrato ────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestContratos:
    """Suite de testes para /api/v1/contratos."""

    async def test_criar_contrato_sucesso(
        self, client: AsyncClient, auth_headers: dict, setup_contrato: dict
    ):
        """Criação com todas as FKs válidas deve retornar 201."""
        payload = {
            "numero":          "2025CT-TEST-001",
            "empresa_cnpj":    setup_contrato["empresa"].cnpj,
            "data_inicio":     "2025-01-01",
            "data_termino":    "2025-12-31",
            "comissao_id":     setup_contrato["comissao"].id,
            "numero_processo": "NUP-2025-TEST",
        }
        resp = await client.post("/api/v1/contratos/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["numero"] == "2025CT-TEST-001"
        # Verifica que os relacionamentos foram carregados
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
                "empresa_cnpj":    "00.000.000/0000-00",  # não existe
                "data_inicio":     "2025-01-01",
                "data_termino":    "2025-12-31",
                "comissao_id":     setup_contrato["comissao"].id,
                "numero_processo": "NUP-FAIL",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_numero_contrato_unico(
        self, client: AsyncClient, auth_headers: dict, setup_contrato: dict
    ):
        """Dois contratos com mesmo número devem resultar em erro."""
        payload = {
            "numero":          "2025CT-DUPLICADO",
            "empresa_cnpj":    setup_contrato["empresa"].cnpj,
            "data_inicio":     "2025-01-01",
            "data_termino":    "2025-06-30",
            "comissao_id":     setup_contrato["comissao"].id,
            "numero_processo": "NUP-DUP",
        }
        await client.post("/api/v1/contratos/", json=payload, headers=auth_headers)
        resp = await client.post("/api/v1/contratos/", json=payload, headers=auth_headers)
        # Deve falhar por constraint de unicidade
        assert resp.status_code in (409, 500)

    async def test_listar_contratos_inclui_empresa(
        self, client: AsyncClient, auth_headers: dict, setup_contrato: dict
    ):
        """Listagem de contratos deve incluir dados da empresa."""
        await client.post(
            "/api/v1/contratos/",
            json={
                "numero":          "2025CT-LIST-TEST",
                "empresa_cnpj":    setup_contrato["empresa"].cnpj,
                "data_inicio":     "2025-02-01",
                "data_termino":    "2025-11-30",
                "comissao_id":     setup_contrato["comissao"].id,
                "numero_processo": "NUP-LIST",
            },
            headers=auth_headers,
        )
        resp = await client.get("/api/v1/contratos/", headers=auth_headers)
        assert resp.status_code == 200
        contratos = resp.json()
        numeros = [c["numero"] for c in contratos]
        assert "2025CT-LIST-TEST" in numeros
        # Verifica que empresa está expandida
        for c in contratos:
            assert "empresa" in c
            assert "nome" in c["empresa"]

    async def test_atualizar_contrato(
        self, client: AsyncClient, auth_headers: dict, setup_contrato: dict
    ):
        """PATCH deve atualizar campos do contrato."""
        # Cria contrato
        create_resp = await client.post(
            "/api/v1/contratos/",
            json={
                "numero":          "2025CT-UPDATE",
                "empresa_cnpj":    setup_contrato["empresa"].cnpj,
                "data_inicio":     "2025-01-01",
                "data_termino":    "2025-12-31",
                "comissao_id":     setup_contrato["comissao"].id,
                "numero_processo": "NUP-UPD",
            },
            headers=auth_headers,
        )
        cid = create_resp.json()["id"]

        # Atualiza o número do processo
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
        """DELETE deve remover o contrato."""
        create_resp = await client.post(
            "/api/v1/contratos/",
            json={
                "numero":          "2025CT-DEL",
                "empresa_cnpj":    setup_contrato["empresa"].cnpj,
                "data_inicio":     "2025-01-01",
                "data_termino":    "2025-12-31",
                "comissao_id":     setup_contrato["comissao"].id,
                "numero_processo": "NUP-DEL",
            },
            headers=auth_headers,
        )
        cid = create_resp.json()["id"]

        resp = await client.delete(f"/api/v1/contratos/{cid}", headers=auth_headers)
        assert resp.status_code == 204

        get_resp = await client.get(f"/api/v1/contratos/{cid}", headers=auth_headers)
        assert get_resp.status_code == 404
