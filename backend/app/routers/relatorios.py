"""
routers/relatorios.py — Relatórios com lógica de franquia por contrato.

Lógica de franquia:
  - A franquia é um TOTAL de páginas para toda a vigência do contrato.
  - A OM paga o valor_mensal_franquia todo mês, use ou não as páginas.
  - Páginas impressas vão consumindo o "balde" da franquia.
  - Quando o balde acaba, as próximas são cobradas por valor_fora_franquia.
  - Em caso de reajuste, usa-se o preço vigente na DATA da leitura (histórico imutável).
"""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import (
    Contrato,
    FranquiaContrato,
    Impressora,
    Leitura,
    TabelaPreco,
)
from app.schemas.schemas import (
    EvolucaoMensalItem,
    RankingImpressora,
    RelatorioMensal,
    RelatorioMensalItem,
    RelatorioTotal,
    RelatorioTotalItem,
)
from app.services.snmp_service import testar_conectividade_snmp

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])

MESES_PT = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _obter_contrato(contrato_id: int, db: AsyncSession) -> Contrato:
    """Busca o contrato ou levanta 404."""
    stmt = (
        select(Contrato)
        .options(
            selectinload(Contrato.empresa),
            selectinload(Contrato.documentos_contabeis),
        )
        .where(Contrato.id == contrato_id)
    )
    result = await db.execute(stmt)
    contrato = result.scalar_one_or_none()
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado.")
    return contrato


def _preco_na_data(
    tabelas: List[TabelaPreco],
    tipo_impressao_id: int,
    data: date,
) -> Tuple[Decimal, Decimal]:
    """
    Retorna (valor_dentro_franquia, valor_fora_franquia) vigente na data informada.

    O histórico garante que reajustes não afetam cálculos de períodos anteriores:
      - vigente_de  : início da validade deste preço
      - vigente_ate : fim da validade (NULL = ainda vigente)

    Se nenhum preço for encontrado, retorna (0, 0) e o relatório mostrará
    aviso de tabela de preços não configurada.
    """
    for tp in sorted(tabelas, key=lambda t: t.vigente_de, reverse=True):
        if tp.tipo_impressao_id != tipo_impressao_id:
            continue
        if tp.vigente_de > data:
            continue
        if tp.vigente_ate is not None and tp.vigente_ate < data:
            continue
        return tp.valor_dentro_franquia, tp.valor_fora_franquia
    return Decimal("0"), Decimal("0")


def _calcular_valor_periodo(
    paginas_periodo: int,
    paginas_acumuladas_antes: int,
    paginas_franquia_total: int,
    valor_dentro: Decimal,
    valor_fora: Decimal,
    valor_mensal_franquia: Decimal,
) -> Tuple[int, int, Decimal, Decimal, Decimal]:
    """
    Calcula os valores financeiros de um período.

    Franquia total é o "balde" do contrato inteiro:
      - Páginas dentro: min(impressas_no_período, saldo_restante_da_franquia)
      - Páginas fora  : impressas_no_período - páginas_dentro (se > 0)

    Retorna: (dentro, fora, custo_fixo_mensal, custo_variavel, total)
    """
    saldo = max(0, paginas_franquia_total - paginas_acumuladas_antes)
    dentro = min(paginas_periodo, saldo)
    fora   = max(0, paginas_periodo - saldo)
    v_var  = Decimal(dentro) * valor_dentro + Decimal(fora) * valor_fora
    total  = valor_mensal_franquia + v_var
    return dentro, fora, valor_mensal_franquia, v_var, total


def _nome_impressora(impressora: Impressora) -> str:
    if impressora.modelo:
        return f"{impressora.modelo.fabricante} {impressora.modelo.modelo}"
    return impressora.num_serie


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/mensal/{contrato_id}", response_model=RelatorioMensal,
            summary="Relatório mensal do contrato")
async def relatorio_mensal(
    contrato_id: int,
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000),
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> RelatorioMensal:
    """
    Relatório mensal com lógica de franquia total do contrato.

    Para cada tipo de impressão:
      1. Calcula páginas acumuladas desde o início do contrato ATÉ o mês anterior
      2. Calcula páginas do mês atual
      3. Aplica ao "balde" da franquia para definir dentro/fora
      4. Usa o preço vigente na data da leitura (respeita histórico de reajustes)
      5. Soma custo fixo mensal (sempre pago) + custo variável
    """
    contrato = await _obter_contrato(contrato_id, db)

    # Carrega franquias e tabelas de preço do contrato
    stmt_franquias = select(FranquiaContrato).where(
        FranquiaContrato.contrato_id == contrato_id
    ).options(selectinload(FranquiaContrato.tipo_impressao))
    franquias = {
        f.tipo_impressao_id: f
        for f in (await db.execute(stmt_franquias)).scalars().all()
    }

    stmt_tabelas = select(TabelaPreco).where(
        TabelaPreco.contrato_id == contrato_id
    )
    tabelas = list((await db.execute(stmt_tabelas)).scalars().all())

    # Leituras do mês atual
    stmt_atual = (
        select(Leitura)
        .options(
            selectinload(Leitura.impressora).selectinload(Impressora.local),
            selectinload(Leitura.impressora).selectinload(Impressora.modelo),
            selectinload(Leitura.tipo_impressao),
        )
        .where(
            and_(
                Leitura.contrato_id == contrato_id,
                Leitura.mes_referencia == mes,
                Leitura.ano_referencia == ano,
            )
        )
    )
    leituras_mes = (await db.execute(stmt_atual)).scalars().all()

    # Leitura do mês anterior (para calcular pages do mês)
    mes_ant = mes - 1 if mes > 1 else 12
    ano_ant = ano if mes > 1 else ano - 1
    stmt_ant = select(Leitura).where(
        and_(
            Leitura.contrato_id == contrato_id,
            Leitura.mes_referencia == mes_ant,
            Leitura.ano_referencia == ano_ant,
        )
    )
    leituras_ant = {
        (l.impressora_num_serie, l.tipo_impressao_id): l
        for l in (await db.execute(stmt_ant)).scalars().all()
    }

    # Páginas acumuladas POR TIPO até o mês anterior (para controle do balde)
    stmt_acum = select(Leitura).where(
        and_(
            Leitura.contrato_id == contrato_id,
            Leitura.ano_referencia * 100 + Leitura.mes_referencia
            < ano * 100 + mes,
        )
    )
    todas_anteriores = (await db.execute(stmt_acum)).scalars().all()

    # Agrupamento de acumulados por tipo e impressora (pares únicos)
    acumulados_tipo: Dict[int, int] = {}
    grupos_ant: Dict[tuple, list] = {}
    for l in sorted(todas_anteriores,
                    key=lambda x: (x.impressora_num_serie, x.tipo_impressao_id,
                                   x.ano_referencia, x.mes_referencia)):
        key = (l.impressora_num_serie, l.tipo_impressao_id)
        grupos_ant.setdefault(key, []).append(l)

    for (ns, tid), lista in grupos_ant.items():
        # Páginas desta impressora/tipo até o mês anterior
        paginas = 0
        for i, leit in enumerate(lista):
            ant = lista[i - 1].contador if i > 0 else 0
            paginas += max(0, leit.contador - ant)
        acumulados_tipo[tid] = acumulados_tipo.get(tid, 0) + paginas

    # Monta itens do relatório
    itens: List[RelatorioMensalItem] = []
    total_paginas = 0
    total_custo_fixo = Decimal("0")
    total_variavel   = Decimal("0")
    total_valor      = Decimal("0")
    total_acumuladas = 0

    # Rastreia quanto cada tipo consumiu neste mês (para atualizar acumulado)
    paginas_mes_por_tipo: Dict[int, int] = {}

    # Agrupa leituras do mês por impressora/tipo
    grupos_mes: Dict[tuple, Leitura] = {}
    for l in leituras_mes:
        grupos_mes[(l.impressora_num_serie, l.tipo_impressao_id)] = l

    for (ns, tid), leit in grupos_mes.items():
        leit_ant = leituras_ant.get((ns, tid))
        contador_ini = leit_ant.contador if leit_ant else 0
        paginas = max(0, leit.contador - contador_ini)

        franquia = franquias.get(tid)
        if not franquia:
            continue  # tipo não configurado neste contrato

        acum_antes = acumulados_tipo.get(tid, 0)
        valor_dentro, valor_fora = _preco_na_data(tabelas, tid, leit.data)

        dentro, fora, v_fixo, v_var, v_total = _calcular_valor_periodo(
            paginas, acum_antes,
            franquia.paginas_franquia,
            valor_dentro, valor_fora,
            franquia.valor_mensal_franquia,
        )

        acum_ate_mes = acum_antes + paginas
        paginas_mes_por_tipo[tid] = paginas_mes_por_tipo.get(tid, 0) + paginas

        itens.append(RelatorioMensalItem(
            impressora_num_serie=ns,
            impressora_nome=_nome_impressora(leit.impressora),
            setor=leit.impressora.local.setor,
            tipo_impressao=leit.tipo_impressao.descricao,
            mes=mes, ano=ano,
            contador_inicial=contador_ini,
            contador_final=leit.contador,
            paginas_impressas=paginas,
            paginas_franquia_total=franquia.paginas_franquia,
            paginas_acumuladas_ate_mes=acum_ate_mes,
            paginas_dentro_franquia=dentro,
            paginas_fora_franquia=fora,
            valor_mensal_franquia=v_fixo,
            valor_dentro_franquia=Decimal(dentro) * valor_dentro,
            valor_fora_franquia=Decimal(fora) * valor_fora,
            valor_total=v_total,
        ))

        total_paginas   += paginas
        total_acumuladas += acum_ate_mes
        total_custo_fixo += v_fixo
        total_variavel   += v_var
        total_valor      += v_total

    # Franquia total contratada (soma de todos os tipos)
    franquia_total_contrato = sum(f.paginas_franquia for f in franquias.values())
    pct_franquia = (
        float(total_acumuladas / franquia_total_contrato * 100)
        if franquia_total_contrato > 0 else 0.0
    )

    total_empenhado = sum(d.valor for d in contrato.documentos_contabeis)
    pct_orcamento = (
        float(total_valor / total_empenhado * 100) if total_empenhado > 0 else 0.0
    )
    hoje = date.today()
    dias_totais = max(1, (contrato.data_termino - contrato.data_inicio).days)
    dias_dec = max(0, (hoje - contrato.data_inicio).days)
    pct_tempo = min(100.0, dias_dec / dias_totais * 100)

    return RelatorioMensal(
        contrato_numero=contrato.numero,
        empresa_nome=contrato.empresa.nome,
        mes=mes, ano=ano,
        itens=itens,
        total_paginas=total_paginas,
        total_paginas_acumuladas=total_acumuladas,
        paginas_franquia_total=franquia_total_contrato,
        percentual_franquia_consumida=round(pct_franquia, 2),
        total_custo_fixo=total_custo_fixo,
        total_variavel=total_variavel,
        total_valor=total_valor,
        percentual_orcamento=round(pct_orcamento, 2),
        percentual_tempo=round(pct_tempo, 2),
    )


@router.get("/total/{contrato_id}", response_model=RelatorioTotal,
            summary="Relatório total do contrato")
async def relatorio_total(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> RelatorioTotal:
    """Relatório consolidado para toda a vigência do contrato."""
    contrato = await _obter_contrato(contrato_id, db)

    stmt_franquias = select(FranquiaContrato).where(
        FranquiaContrato.contrato_id == contrato_id
    ).options(selectinload(FranquiaContrato.tipo_impressao))
    franquias = {
        f.tipo_impressao_id: f
        for f in (await db.execute(stmt_franquias)).scalars().all()
    }

    stmt_tabelas = select(TabelaPreco).where(TabelaPreco.contrato_id == contrato_id)
    tabelas = list((await db.execute(stmt_tabelas)).scalars().all())

    stmt_leituras = (
        select(Leitura)
        .where(Leitura.contrato_id == contrato_id)
        .options(
            selectinload(Leitura.impressora).selectinload(Impressora.modelo),
            selectinload(Leitura.tipo_impressao),
        )
        .order_by(
            Leitura.impressora_num_serie, Leitura.tipo_impressao_id,
            Leitura.ano_referencia, Leitura.mes_referencia,
        )
    )
    todas = (await db.execute(stmt_leituras)).scalars().all()

    # Agrupa por (impressora, tipo)
    grupos: Dict[tuple, list] = {}
    for l in todas:
        grupos.setdefault((l.impressora_num_serie, l.tipo_impressao_id), []).append(l)

    totais_tipo: Dict[str, Dict] = {}
    acumulados_tipo: Dict[int, int] = {}
    meses_unicos: set = set()
    impressoras_ativas: set = set()

    for (ns, tid), lista in grupos.items():
        franquia = franquias.get(tid)
        if not franquia:
            continue
        descricao = lista[0].tipo_impressao.descricao

        for i, leit in enumerate(lista):
            ant = lista[i - 1].contador if i > 0 else 0
            paginas = max(0, leit.contador - ant)
            valor_dentro, valor_fora = _preco_na_data(tabelas, tid, leit.data)

            acum = acumulados_tipo.get(tid, 0)
            dentro, fora, v_fixo, v_var, v_total = _calcular_valor_periodo(
                paginas, acum,
                franquia.paginas_franquia,
                valor_dentro, valor_fora,
                franquia.valor_mensal_franquia,
            )
            acumulados_tipo[tid] = acum + paginas

            entrada = totais_tipo.setdefault(descricao, {
                "paginas": 0, "valor": Decimal("0"),
                "franquia_total": franquia.paginas_franquia,
            })
            entrada["paginas"] += paginas
            entrada["valor"]   += v_total
            meses_unicos.add((leit.mes_referencia, leit.ano_referencia))
            impressoras_ativas.add(ns)

    itens = [
        RelatorioTotalItem(
            tipo_impressao=desc,
            total_paginas=d["paginas"],
            total_valor=d["valor"],
        )
        for desc, d in totais_tipo.items()
    ]

    total_paginas = sum(i.total_paginas for i in itens)
    total_valor   = sum(i.total_valor   for i in itens)
    total_empenhado = sum(d.valor for d in contrato.documentos_contabeis)
    pct_orcamento = float(total_valor / total_empenhado * 100) if total_empenhado > 0 else 0.0

    hoje = date.today()
    dias_totais = max(1, (contrato.data_termino - contrato.data_inicio).days)
    dias_dec    = max(0, min(dias_totais, (hoje - contrato.data_inicio).days))
    pct_tempo   = dias_dec / dias_totais * 100

    return RelatorioTotal(
        contrato_numero=contrato.numero,
        empresa_nome=contrato.empresa.nome,
        data_inicio=contrato.data_inicio,
        data_termino=contrato.data_termino,
        numero_processo=contrato.numero_processo,
        valor_estimado=contrato.valor_estimado,
        itens=itens,
        total_geral_paginas=total_paginas,
        total_geral_valor=total_valor,
        total_empenhado=total_empenhado,
        percentual_orcamento_consumido=round(pct_orcamento, 2),
        percentual_tempo_decorrido=round(pct_tempo, 2),
        dias_decorridos=dias_dec,
        dias_totais=dias_totais,
        meses_com_leitura=len(meses_unicos),
        impressoras_ativas=len(impressoras_ativas),
    )


@router.get("/evolucao/{contrato_id}", response_model=List[EvolucaoMensalItem],
            summary="Evolução mensal (para gráficos)")
async def evolucao_mensal(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> List[EvolucaoMensalItem]:
    """Série temporal mensal de páginas e valores para gráficos."""
    await _obter_contrato(contrato_id, db)

    stmt_franquias = select(FranquiaContrato).where(FranquiaContrato.contrato_id == contrato_id)
    franquias = {f.tipo_impressao_id: f for f in (await db.execute(stmt_franquias)).scalars().all()}

    stmt_tabelas = select(TabelaPreco).where(TabelaPreco.contrato_id == contrato_id)
    tabelas = list((await db.execute(stmt_tabelas)).scalars().all())

    stmt = (
        select(Leitura)
        .where(Leitura.contrato_id == contrato_id)
        .order_by(Leitura.impressora_num_serie, Leitura.tipo_impressao_id,
                  Leitura.ano_referencia, Leitura.mes_referencia)
    )
    todas = (await db.execute(stmt)).scalars().all()

    grupos: Dict[tuple, list] = {}
    for l in todas:
        grupos.setdefault((l.impressora_num_serie, l.tipo_impressao_id), []).append(l)

    meses: Dict[tuple, Dict] = {}
    acumulados_tipo: Dict[int, int] = {}

    for (ns, tid), lista in grupos.items():
        franquia = franquias.get(tid)
        if not franquia:
            continue
        for i, leit in enumerate(lista):
            ant = lista[i - 1].contador if i > 0 else 0
            paginas = max(0, leit.contador - ant)
            valor_dentro, valor_fora = _preco_na_data(tabelas, tid, leit.data)
            acum = acumulados_tipo.get(tid, 0)
            _, _, v_fixo, v_var, v_total = _calcular_valor_periodo(
                paginas, acum, franquia.paginas_franquia,
                valor_dentro, valor_fora, franquia.valor_mensal_franquia,
            )
            acumulados_tipo[tid] = acum + paginas
            key = (leit.ano_referencia, leit.mes_referencia)
            e = meses.setdefault(key, {"paginas": 0, "valor": Decimal("0")})
            e["paginas"] += paginas
            e["valor"]   += v_total

    return [
        EvolucaoMensalItem(
            mes=mes, ano=ano,
            label=f"{MESES_PT[mes]}/{ano}",
            total_paginas=d["paginas"],
            total_valor=d["valor"],
        )
        for (ano, mes), d in sorted(meses.items())
    ]


@router.get("/ranking/{contrato_id}", response_model=List[RankingImpressora],
            summary="Ranking de impressoras por volume")
async def ranking_impressoras(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> List[RankingImpressora]:
    """Impressoras ordenadas pelo volume total de páginas impressas."""
    await _obter_contrato(contrato_id, db)

    stmt_franquias = select(FranquiaContrato).where(FranquiaContrato.contrato_id == contrato_id)
    franquias = {f.tipo_impressao_id: f for f in (await db.execute(stmt_franquias)).scalars().all()}

    stmt_tabelas = select(TabelaPreco).where(TabelaPreco.contrato_id == contrato_id)
    tabelas = list((await db.execute(stmt_tabelas)).scalars().all())

    stmt = (
        select(Leitura)
        .where(Leitura.contrato_id == contrato_id)
        .options(
            selectinload(Leitura.impressora).selectinload(Impressora.local),
            selectinload(Leitura.impressora).selectinload(Impressora.modelo),
        )
        .order_by(Leitura.impressora_num_serie, Leitura.tipo_impressao_id,
                  Leitura.ano_referencia, Leitura.mes_referencia)
    )
    todas = (await db.execute(stmt)).scalars().all()

    grupos: Dict[tuple, list] = {}
    for l in todas:
        grupos.setdefault((l.impressora_num_serie, l.tipo_impressao_id), []).append(l)

    por_impressora: Dict[str, Dict] = {}
    acumulados_tipo: Dict[int, int] = {}

    for (ns, tid), lista in grupos.items():
        franquia = franquias.get(tid)
        if not franquia:
            continue
        imp = lista[0].impressora
        for i, leit in enumerate(lista):
            ant = lista[i - 1].contador if i > 0 else 0
            paginas = max(0, leit.contador - ant)
            valor_dentro, valor_fora = _preco_na_data(tabelas, tid, leit.data)
            acum = acumulados_tipo.get(tid, 0)
            _, _, _, _, v_total = _calcular_valor_periodo(
                paginas, acum, franquia.paginas_franquia,
                valor_dentro, valor_fora, franquia.valor_mensal_franquia,
            )
            acumulados_tipo[tid] = acum + paginas
            e = por_impressora.setdefault(ns, {
                "nome": _nome_impressora(imp),
                "setor": imp.local.setor,
                "paginas": 0, "valor": Decimal("0"),
            })
            e["paginas"] += paginas
            e["valor"]   += v_total

    ranking = sorted(por_impressora.items(), key=lambda x: x[1]["paginas"], reverse=True)
    return [
        RankingImpressora(
            posicao=i + 1, num_serie=ns,
            nome=d["nome"], setor=d["setor"],
            total_paginas=d["paginas"], total_valor=d["valor"],
        )
        for i, (ns, d) in enumerate(ranking)
    ]


@router.get("/snmp-teste/{num_serie}", summary="Testa conectividade SNMP")
async def testar_snmp(
    num_serie: str,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> dict:
    """Testa se a impressora está acessível via SNMP."""
    from app.models.models import Impressora as ImpressoraModel
    imp = await db.get(ImpressoraModel, num_serie)
    if not imp:
        raise HTTPException(status_code=404, detail="Impressora não encontrada.")
    if not imp.ip:
        raise HTTPException(status_code=422, detail="Impressora sem IP configurado.")
    resultado = await testar_conectividade_snmp(imp.ip)
    return {"impressora": num_serie, "ip": imp.ip, **resultado}
