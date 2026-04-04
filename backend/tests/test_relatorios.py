"""
tests/test_relatorios.py — Testes dos endpoints de relatórios.

Nova lógica de franquia:
  - TipoImpressao tem apenas descrição
  - Franquia total do contrato definida em FranquiaContrato
  - Preços unitários em TabelaPreco (com histórico de reajustes)
  - Leituras vinculadas ao contrato_id

Fixture contrato_completo monta:
  - Contrato de 1 ano (Jan–Dez 2025), R$20.000 empenhados
  - TipoImpressão P&B A4 com franquia de 30.000 páginas totais
  - Custo fixo: R$500/mês; dentro: R$0,04/pág; fora: R$0,08/pág
  - 3 leituras: Jan(0→6.000), Fev(6.000→11.500), Mar(11.500→16.000) = 16.000 páginas
  - Acumulado 16.000 páginas < franquia de 30.000 → tudo dentro da franquia
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
    FranquiaContrato,
    Impressora,
    Leitura,
    LocalImpressora,
    Membro,
    ModeloImpressora,
    TabelaPreco,
    TipoDoc,
    TipoImpressao,
    TipoImpressora,
)


@pytest_asyncio.fixture
async def contrato_completo(db: AsyncSession) -> dict:
    """
    Cenário completo para testes de relatório com nova lógica de franquia.

    Valores:
      - Franquia total: 30.000 páginas para toda a vigência
      - Custo fixo: R$ 500,00/mês (pago sempre)
      - Dentro da franquia: R$ 0,04/pág
      - Fora da franquia:   R$ 0,08/pág
      - Leituras: Jan(6.000), Fev(5.500), Mar(4.500) = 16.000 páginas acumuladas
      - Todas dentro da franquia (16.000 < 30.000)

    Custo Jan: 500 + (6.000 × 0,04) = 500 + 240 = 740,00
    Custo Fev: 500 + (5.500 × 0,04) = 500 + 220 = 720,00
    Custo Mar: 500 + (4.500 × 0,04) = 500 + 180 = 680,00
    Total 3 meses: 2.140,00
    """
    empresa = Empresa(cnpj="99.888.777-0001-66", nome="Gráfica Militar LTDA")
    membro  = Membro(cpf="000.111.222-33", nome="Ten Coronel Ferreira")
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
        numero="CONTRATO-REL-001",
        empresa_cnpj=empresa.cnpj,
        data_inicio=date(2025, 1, 1),
        data_termino=date(2025, 12, 31),
        comissao_id=comissao.id,
        numero_processo="NUP-REL-001",
        valor_estimado=Decimal("20000.00"),
    )
    db.add(contrato)
    await db.flush()

    tipo_doc = TipoDoc(nome="NE-REL")
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
    local    = LocalImpressora(setor="SETIC", descricao="Sala de Impressão")
    modelo   = ModeloImpressora(fabricante="HP", modelo="LaserJet M404n")
    db.add_all([tipo_imp, local, modelo])
    await db.flush()

    impressora = Impressora(
        num_serie="HP-REL-001",
        tipo_id=tipo_imp.id,
        local_id=local.id,
        modelo_id=modelo.id,
        ip="192.168.0.10",
        ativa=True,
    )
    db.add(impressora)

    ti = TipoImpressao(descricao="P&B A4 Franquia")
    db.add(ti)
    await db.flush()

    # Franquia: 30.000 páginas totais, R$500/mês custo fixo
    franquia = FranquiaContrato(
        contrato_id=contrato.id,
        tipo_impressao_id=ti.id,
        paginas_franquia=30_000,
        valor_mensal_franquia=Decimal("500.00"),
    )
    db.add(franquia)

    # Tabela de preços inicial (vigente desde 01/01/2025, sem data de fim)
    tabela = TabelaPreco(
        contrato_id=contrato.id,
        tipo_impressao_id=ti.id,
        valor_dentro_franquia=Decimal("0.04"),
        valor_fora_franquia=Decimal("0.08"),
        vigente_de=date(2025, 1, 1),
        vigente_ate=None,
    )
    db.add(tabela)
    await db.flush()

    # Leituras: Jan(0→6.000), Fev(6.000→11.500), Mar(11.500→16.000)
    leituras = [
        Leitura(
            contrato_id=contrato.id,
            impressora_num_serie=impressora.num_serie,
            tipo_impressao_id=ti.id,
            contador=6000,
            data=date(2025, 1, 31),
            mes_referencia=1, ano_referencia=2025, manual=False,
        ),
        Leitura(
            contrato_id=contrato.id,
            impressora_num_serie=impressora.num_serie,
            tipo_impressao_id=ti.id,
            contador=11500,
            data=date(2025, 2, 28),
            mes_referencia=2, ano_referencia=2025, manual=False,
        ),
        Leitura(
            contrato_id=contrato.id,
            impressora_num_serie=impressora.num_serie,
            tipo_impressao_id=ti.id,
            contador=16000,
            data=date(2025, 3, 31),
            mes_referencia=3, ano_referencia=2025, manual=False,
        ),
    ]
    db.add_all(leituras)
    await db.flush()

    return {
        "contrato":      contrato,
        "impressora":    impressora,
        "tipo_impressao": ti,
        "franquia":      franquia,
        "tabela":        tabela,
        "empenho":       Decimal("10000.00"),
    }


@pytest.mark.asyncio
class TestRelatorioMensal:
    """Testes do endpoint GET /relatorios/mensal/{contrato_id}."""

    async def test_retorna_200(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Relatório mensal de contrato existente deve retornar 200."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(
            f"/api/v1/relatorios/mensal/{cid}?mes=1&ano=2025",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    async def test_calcula_paginas_corretamente(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Janeiro: contador 0→6.000 = 6.000 páginas impressas."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(
            f"/api/v1/relatorios/mensal/{cid}?mes=1&ano=2025",
            headers=auth_headers,
        )
        assert resp.json()["total_paginas"] == 6000

    async def test_calcula_custo_fixo_mensal(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Custo fixo mensal deve ser R$500 independente das páginas impressas."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(
            f"/api/v1/relatorios/mensal/{cid}?mes=1&ano=2025",
            headers=auth_headers,
        )
        data = resp.json()
        # custo fixo = R$500
        assert float(data["total_custo_fixo"]) == pytest.approx(500.0)

    async def test_calcula_valor_variavel_dentro_franquia(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """
        Janeiro: 6.000 pág × R$0,04 = R$240 variável.
        Total: R$500 + R$240 = R$740.
        """
        cid = contrato_completo["contrato"].id
        resp = await client.get(
            f"/api/v1/relatorios/mensal/{cid}?mes=1&ano=2025",
            headers=auth_headers,
        )
        data = resp.json()
        assert float(data["total_variavel"]) == pytest.approx(240.0)
        assert float(data["total_valor"])    == pytest.approx(740.0)

    async def test_paginas_dentro_e_fora_franquia(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """
        Janeiro: 6.000 págs acumuladas, franquia 30.000 → todas dentro.
        Nenhuma página fora da franquia.
        """
        cid = contrato_completo["contrato"].id
        resp = await client.get(
            f"/api/v1/relatorios/mensal/{cid}?mes=1&ano=2025",
            headers=auth_headers,
        )
        item = resp.json()["itens"][0]
        assert item["paginas_dentro_franquia"] == 6000
        assert item["paginas_fora_franquia"]   == 0

    async def test_percentual_franquia_consumida(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """
        Após Janeiro: acumulado=6.000, franquia=30.000 → 20% consumido.
        """
        cid = contrato_completo["contrato"].id
        resp = await client.get(
            f"/api/v1/relatorios/mensal/{cid}?mes=1&ano=2025",
            headers=auth_headers,
        )
        data = resp.json()
        assert data["percentual_franquia_consumida"] == pytest.approx(20.0, rel=0.01)

    async def test_acumulado_cresce_entre_meses(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Acumulado em Março deve ser Jan+Fev+Mar = 16.000 páginas."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(
            f"/api/v1/relatorios/mensal/{cid}?mes=3&ano=2025",
            headers=auth_headers,
        )
        data = resp.json()
        # Mar: contador 11.500→16.000 = 4.500 págs
        assert data["total_paginas"] == 4500
        # Acumulado total: 6.000 + 5.500 + 4.500 = 16.000
        assert data["total_paginas_acumuladas"] == 16000

    async def test_percentual_tempo(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Percentual de tempo deve estar entre 0 e 100."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(
            f"/api/v1/relatorios/mensal/{cid}?mes=1&ano=2025",
            headers=auth_headers,
        )
        pct = resp.json()["percentual_tempo"]
        assert 0 <= pct <= 100

    async def test_contrato_inexistente_retorna_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Relatório para contrato inexistente deve retornar 404."""
        resp = await client.get(
            "/api/v1/relatorios/mensal/99999?mes=1&ano=2025",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_mes_sem_leituras_retorna_lista_vazia(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Mês sem leituras deve retornar 200 com itens=[]."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(
            f"/api/v1/relatorios/mensal/{cid}?mes=12&ano=2025",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["itens"] == []
        assert resp.json()["total_paginas"] == 0


@pytest.mark.asyncio
class TestRelatorioTotal:
    """Testes do endpoint GET /relatorios/total/{contrato_id}."""

    async def test_retorna_200_com_estrutura(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Relatório total deve retornar 200 com campos obrigatórios."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(f"/api/v1/relatorios/total/{cid}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_geral_paginas" in data
        assert "percentual_orcamento_consumido" in data
        assert "percentual_tempo_decorrido" in data
        assert "dias_totais" in data
        assert data["dias_totais"] > 0

    async def test_soma_todos_os_meses(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """
        3 meses de leitura:
          Jan: 6.000 | Fev: 5.500 | Mar: 4.500 = 16.000 páginas total.
        """
        cid = contrato_completo["contrato"].id
        resp = await client.get(f"/api/v1/relatorios/total/{cid}", headers=auth_headers)
        assert resp.json()["total_geral_paginas"] == 16000

    async def test_percentual_orcamento_nao_negativo(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Percentual de orçamento consumido nunca pode ser negativo."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(f"/api/v1/relatorios/total/{cid}", headers=auth_headers)
        assert resp.json()["percentual_orcamento_consumido"] >= 0

    async def test_meses_com_leitura(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Deve contabilizar os 3 meses com leitura (Jan, Fev, Mar)."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(f"/api/v1/relatorios/total/{cid}", headers=auth_headers)
        assert resp.json()["meses_com_leitura"] == 3

    async def test_impressoras_ativas(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Deve contar 1 impressora ativa com leituras."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(f"/api/v1/relatorios/total/{cid}", headers=auth_headers)
        assert resp.json()["impressoras_ativas"] == 1


@pytest.mark.asyncio
class TestEvolucaoMensal:
    """Testes do endpoint GET /relatorios/evolucao/{contrato_id}."""

    async def test_retorna_lista_ordenada_cronologicamente(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Evolução deve retornar itens em ordem cronológica (Jan→Fev→Mar)."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(f"/api/v1/relatorios/evolucao/{cid}", headers=auth_headers)
        assert resp.status_code == 200
        itens = resp.json()
        assert len(itens) == 3
        assert itens[0]["mes"] == 1
        assert itens[1]["mes"] == 2
        assert itens[2]["mes"] == 3

    async def test_labels_formatados(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Labels devem estar no formato 'Mês/Ano' (ex: Jan/2025)."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(f"/api/v1/relatorios/evolucao/{cid}", headers=auth_headers)
        labels = [i["label"] for i in resp.json()]
        assert "Jan/2025" in labels
        assert "Fev/2025" in labels
        assert "Mar/2025" in labels

    async def test_valores_crescem_com_paginas(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Cada mês deve ter valor > 0 (custo fixo + variável)."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(f"/api/v1/relatorios/evolucao/{cid}", headers=auth_headers)
        for item in resp.json():
            assert float(item["total_valor"]) > 0


@pytest.mark.asyncio
class TestRankingImpressoras:
    """Testes do endpoint GET /relatorios/ranking/{contrato_id}."""

    async def test_retorna_posicoes_ordenadas(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Ranking deve retornar impressoras com posição numérica sequencial."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(f"/api/v1/relatorios/ranking/{cid}", headers=auth_headers)
        assert resp.status_code == 200
        itens = resp.json()
        assert len(itens) >= 1
        assert itens[0]["posicao"] == 1

    async def test_impressora_mais_usada_em_primeiro(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """A única impressora do cenário deve estar na posição 1."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(f"/api/v1/relatorios/ranking/{cid}", headers=auth_headers)
        ranking = resp.json()
        assert ranking[0]["num_serie"] == contrato_completo["impressora"].num_serie
        assert ranking[0]["total_paginas"] == 16000


@pytest.mark.asyncio
class TestFranquiasEndpoints:
    """Testes dos endpoints de franquias e tabelas de preço."""

    async def test_listar_franquias_do_contrato(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """GET /franquias/{contrato_id} deve retornar a franquia configurada."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(f"/api/v1/franquias/{cid}", headers=auth_headers)
        assert resp.status_code == 200
        franquias = resp.json()
        assert len(franquias) == 1
        assert franquias[0]["paginas_franquia"] == 30000
        assert float(franquias[0]["valor_mensal_franquia"]) == 500.0

    async def test_listar_tabelas_preco(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """GET /tabelas-preco/{contrato_id} deve retornar o preço configurado."""
        cid = contrato_completo["contrato"].id
        resp = await client.get(f"/api/v1/tabelas-preco/{cid}", headers=auth_headers)
        assert resp.status_code == 200
        tabelas = resp.json()
        assert len(tabelas) == 1
        assert float(tabelas[0]["valor_dentro_franquia"]) == pytest.approx(0.04)
        assert float(tabelas[0]["valor_fora_franquia"]) == pytest.approx(0.08)
        assert tabelas[0]["vigente_ate"] is None  # preço vigente atual

    async def test_criar_franquia(
        self, client: AsyncClient, auth_headers: dict, contrato_base: Contrato,
        tipo_impressao: TipoImpressao,
    ):
        """POST /franquias/ deve criar nova franquia e retornar 201."""
        resp = await client.post(
            "/api/v1/franquias/",
            json={
                "contrato_id":            contrato_base.id,
                "tipo_impressao_id":      tipo_impressao.id,
                "paginas_franquia":       50000,
                "valor_mensal_franquia":  1500.00,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["paginas_franquia"] == 50000
        assert float(data["valor_mensal_franquia"]) == 1500.0

    async def test_reajuste_cria_historico(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """
        POST /tabelas-preco/{id}/reajuste deve:
        1. Fechar o preço atual (vigente_ate = data_reajuste - 1 dia)
        2. Criar novo preço com vigente_ate=None
        3. Histórico deve ter 2 registros
        """
        cid = contrato_completo["contrato"].id
        tid = contrato_completo["tipo_impressao"].id

        resp = await client.post(
            f"/api/v1/tabelas-preco/{cid}/reajuste",
            json={
                "tipo_impressao_id":     tid,
                "valor_dentro_franquia": 0.045,
                "valor_fora_franquia":   0.090,
                "vigente_de":            "2025-07-01",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        novo = resp.json()
        assert float(novo["valor_dentro_franquia"]) == pytest.approx(0.045)
        assert novo["vigente_ate"] is None  # novo preço vigente

        # Verifica que agora há 2 registros (histórico + novo)
        lista = await client.get(f"/api/v1/tabelas-preco/{cid}", headers=auth_headers)
        tabelas = lista.json()
        assert len(tabelas) == 2
        vigentes = [t for t in tabelas if t["vigente_ate"] is None]
        historicos = [t for t in tabelas if t["vigente_ate"] is not None]
        assert len(vigentes) == 1
        assert len(historicos) == 1

    async def test_reajuste_data_anterior_retorna_422(
        self, client: AsyncClient, auth_headers: dict, contrato_completo: dict
    ):
        """Reajuste com data anterior ao preço atual deve retornar 422."""
        cid = contrato_completo["contrato"].id
        tid = contrato_completo["tipo_impressao"].id

        resp = await client.post(
            f"/api/v1/tabelas-preco/{cid}/reajuste",
            json={
                "tipo_impressao_id":     tid,
                "valor_dentro_franquia": 0.05,
                "valor_fora_franquia":   0.10,
                "vigente_de":            "2024-01-01",  # anterior ao início do preço
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422
