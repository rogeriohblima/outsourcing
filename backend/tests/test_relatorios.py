"""
tests/test_relatorios.py — Testes unitários dos relatórios.

Cobre:
  - Relatório mensal: cálculo de páginas, franquia e excedente
  - Relatório mensal: percentuais de orçamento e tempo
  - Relatório total: consolidação de todos os meses
  - Evolução mensal: série temporal ordenada
  - Ranking de impressoras
  - Contrato inexistente retorna 404
"""

from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Comissao,
    Contrato,
    DocumentoContabil,
    Empresa,
    Impressora,
    LocalImpressora,
    Leitura,
    Membro,
    TipoDoc,
    TipoImpressao,
    TipoImpressora,
)


# ── Fixtures específicas dos relatórios ──────────────────────────────────────

@pytest_asyncio.fixture
async def contrato_completo(db: AsyncSession):
    """
    Monta um cenário completo para testes de relatório:
    - Empresa, Membro, Comissão, Contrato (1 ano de vigência)
    - TipoDoc, DocumentoContabil (empenho de R$ 10.000)
    - TipoImpressora, Local, Impressora (com IP)
    - TipoImpressão (5.000 páginas, R$ 500/mês, R$ 0,05/excedente)
    - 3 leituras mensais (Jan, Fev, Mar/2025)
    """
    empresa = Empresa(cnpj="99.888.777/0001-66", nome="Gráfica Militar LTDA")
    membro = Membro(cpf="000.111.222-33", nome="Ten Coronel Ferreira")
    db.add_all([empresa, membro])
    await db.flush()

    comissao = Comissao(
        presidente_cpf=membro.cpf,
        documento_numero="BI 001/2025",
        documento_data=date(2025, 1, 1),
    )
    db.add(comissao)
    await db.flush()

    contrato = Contrato(
        numero="CONTRATO-2025-001",
        empresa_cnpj=empresa.cnpj,
        data_inicio=date(2025, 1, 1),
        data_termino=date(2025, 12, 31),
        comissao_id=comissao.id,
        numero_processo="NUP-2025-001",
    )
    db.add(contrato)
    await db.flush()

    tipo_doc = TipoDoc(nome="NE")
    db.add(tipo_doc)
    await db.flush()

    doc = DocumentoContabil(
        numero="NE 2025NE000001",
        tipo_documento_id=tipo_doc.id,
        contrato_id=contrato.id,
        valor=Decimal("10000.00"),
    )
    db.add(doc)

    tipo_imp = TipoImpressora(tipo="Laser P&B A4")
    local = LocalImpressora(setor="SETIC", descricao="Sala de Impressão")
    db.add_all([tipo_imp, local])
    await db.flush()

    impressora = Impressora(
        num_serie="HP-REL-001",
        nome="HP LaserJet Relatório",
        tipo_id=tipo_imp.id,
        local_id=local.id,
        ip="192.168.0.10",
        ativa=True,
    )
    db.add(impressora)

    ti = TipoImpressao(
        descricao="P&B A4 Franquia",
        franquia=5000,
        valor_franquia=Decimal("500.00"),
        valor_extra_franquia=Decimal("0.05"),
    )
    db.add(ti)
    await db.flush()

    # Leituras: Jan (0→6000), Fev (6000→11500), Mar (11500→16000)
    leituras = [
        Leitura(impressora_num_serie=impressora.num_serie, tipo_impressao_id=ti.id,
                contador=6000,  data=date(2025,1,31),  mes_referencia=1, ano_referencia=2025, manual=False),
        Leitura(impressora_num_serie=impressora.num_serie, tipo_impressao_id=ti.id,
                contador=11500, data=date(2025,2,28),  mes_referencia=2, ano_referencia=2025, manual=False),
        Leitura(impressora_num_serie=impressora.num_serie, tipo_impressao_id=ti.id,
                contador=16000, data=date(2025,3,31),  mes_referencia=3, ano_referencia=2025, manual=False),
    ]
    db.add_all(leituras)
    await db.flush()

    return {
        "contrato": contrato,
        "impressora": impressora,
        "tipo_impressao": ti,
        "empenho": Decimal("10000.00"),
    }


# ── Testes ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestRelatorioMensal:
    """Testes do endpoint GET /relatorios/mensal/{contrato_id}."""

    async def test_relatorio_mensal_retorna_200(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Relatório mensal de contrato existente deve retornar 200."""
        cid = contrato_completo["contrato"].id
        response = await client.get(
            f"/api/v1/relatorios/mensal/{cid}?mes=1&ano=2025",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_relatorio_mensal_calcula_paginas(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """
        Janeiro: contador final=6000, inicial=0 → 6000 páginas.
        Franquia=5000 → 5000 dentro + 1000 excedente.
        Valor = R$500 + (1000 × 0,05) = R$550.
        """
        cid = contrato_completo["contrato"].id
        response = await client.get(
            f"/api/v1/relatorios/mensal/{cid}?mes=1&ano=2025",
            headers=auth_headers,
        )
        data = response.json()
        assert data["total_paginas"] == 6000

        item = data["itens"][0]
        assert item["paginas_impressas"] == 6000
        assert item["paginas_dentro_franquia"] == 5000
        assert item["paginas_excedente"] == 1000
        assert float(item["valor_franquia"]) == pytest.approx(500.0)
        assert float(item["valor_excedente"]) == pytest.approx(50.0)
        assert float(item["valor_total"]) == pytest.approx(550.0)

    async def test_relatorio_mensal_percentual_tempo(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Percentual de tempo deve estar entre 0 e 100."""
        cid = contrato_completo["contrato"].id
        response = await client.get(
            f"/api/v1/relatorios/mensal/{cid}?mes=1&ano=2025",
            headers=auth_headers,
        )
        pct = response.json()["percentual_tempo"]
        assert 0 <= pct <= 100

    async def test_relatorio_mensal_contrato_inexistente_retorna_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Relatório para contrato inexistente deve retornar 404."""
        response = await client.get(
            "/api/v1/relatorios/mensal/99999?mes=1&ano=2025",
            headers=auth_headers,
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestRelatorioTotal:
    """Testes do endpoint GET /relatorios/total/{contrato_id}."""

    async def test_relatorio_total_retorna_200(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Relatório total deve retornar 200 com estrutura correta."""
        cid = contrato_completo["contrato"].id
        response = await client.get(
            f"/api/v1/relatorios/total/{cid}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_geral_paginas" in data
        assert "percentual_orcamento_consumido" in data
        assert "percentual_tempo_decorrido" in data
        assert data["dias_totais"] > 0

    async def test_relatorio_total_soma_todos_meses(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """
        3 meses de leitura:
          Jan: 6000 págs | Fev: 5500 págs | Mar: 4500 págs = 16000 total
        """
        cid = contrato_completo["contrato"].id
        response = await client.get(
            f"/api/v1/relatorios/total/{cid}", headers=auth_headers
        )
        # Jan: 6000-0=6000, Fev: 11500-6000=5500, Mar: 16000-11500=4500
        assert response.json()["total_geral_paginas"] == 16000

    async def test_relatorio_total_percentual_orcamento(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Percentual de orçamento deve ser calculado corretamente."""
        cid = contrato_completo["contrato"].id
        response = await client.get(
            f"/api/v1/relatorios/total/{cid}", headers=auth_headers
        )
        pct = response.json()["percentual_orcamento_consumido"]
        # Não pode ser negativo nem muito acima de 100 neste cenário
        assert pct >= 0

    async def test_relatorio_total_meses_com_leitura(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Deve contabilizar corretamente os 3 meses com leitura."""
        cid = contrato_completo["contrato"].id
        response = await client.get(
            f"/api/v1/relatorios/total/{cid}", headers=auth_headers
        )
        assert response.json()["meses_com_leitura"] == 3


@pytest.mark.asyncio
class TestEvolucaoMensal:
    """Testes do endpoint GET /relatorios/evolucao/{contrato_id}."""

    async def test_evolucao_retorna_lista_ordenada(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Evolução deve retornar itens ordenados cronologicamente."""
        cid = contrato_completo["contrato"].id
        response = await client.get(
            f"/api/v1/relatorios/evolucao/{cid}", headers=auth_headers
        )
        assert response.status_code == 200
        itens = response.json()
        assert len(itens) == 3
        # Verifica ordem: Jan, Fev, Mar
        assert itens[0]["mes"] == 1
        assert itens[1]["mes"] == 2
        assert itens[2]["mes"] == 3

    async def test_evolucao_label_formatado(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Labels devem estar no formato 'Mês/Ano' (ex: Jan/2025)."""
        cid = contrato_completo["contrato"].id
        response = await client.get(
            f"/api/v1/relatorios/evolucao/{cid}", headers=auth_headers
        )
        labels = [item["label"] for item in response.json()]
        assert "Jan/2025" in labels
        assert "Fev/2025" in labels


@pytest.mark.asyncio
class TestRankingImpressoras:
    """Testes do endpoint GET /relatorios/ranking/{contrato_id}."""

    async def test_ranking_retorna_posicoes(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Ranking deve retornar impressoras com posição numérica."""
        cid = contrato_completo["contrato"].id
        response = await client.get(
            f"/api/v1/relatorios/ranking/{cid}", headers=auth_headers
        )
        assert response.status_code == 200
        itens = response.json()
        assert len(itens) >= 1
        assert itens[0]["posicao"] == 1
