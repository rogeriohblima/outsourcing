"""
routers/relatorios.py — Endpoints de relatórios mensais e totais.

Endpoints:
  GET /relatorios/mensal/{contrato_id}        — Relatório mensal de um contrato
  GET /relatorios/total/{contrato_id}         — Relatório total do contrato
  GET /relatorios/evolucao/{contrato_id}      — Evolução mensal (para gráficos)
  GET /relatorios/ranking/{contrato_id}       — Ranking de impressoras por volume
  GET /relatorios/snmp-teste/{num_serie}      — Testa conectividade SNMP
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import (
    Contrato,
    DocumentoContabil,
    Impressora,
    Leitura,
    LocalImpressora,
    TipoImpressao,
    TipoImpressora,
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

MESES_PT = [
    "", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
]


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


def _calcular_valor_impressao(
    paginas: int,
    franquia: int,
    valor_franquia: Decimal,
    valor_extra: Decimal,
) -> tuple[int, int, Decimal, Decimal, Decimal]:
    """
    Calcula os valores financeiros de um período de impressão.

    Returns:
        (dentro_franquia, excedente, valor_franq, valor_exc, valor_total)
    """
    dentro = min(paginas, franquia)
    excedente = max(0, paginas - franquia)
    valor_exc = Decimal(excedente) * valor_extra
    total = valor_franquia + valor_exc
    return dentro, excedente, valor_franquia, valor_exc, total


@router.get(
    "/mensal/{contrato_id}",
    response_model=RelatorioMensal,
    summary="Relatório mensal do contrato",
)
async def relatorio_mensal(
    contrato_id: int,
    mes: int = Query(..., ge=1, le=12, description="Mês de referência"),
    ano: int = Query(..., ge=2000, description="Ano de referência"),
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> RelatorioMensal:
    """
    Gera o relatório mensal de impressão para um contrato.

    Para cada impressora/tipo de impressão, calcula:
    - Páginas impressas no mês (diferença entre leitura atual e anterior)
    - Páginas dentro e fora da franquia
    - Valores financeiros correspondentes
    - Percentual de orçamento consumido e tempo decorrido
    """
    contrato = await _obter_contrato(contrato_id, db)

    # Leituras do mês de referência
    stmt_atual = (
        select(Leitura)
        .options(
            selectinload(Leitura.impressora).selectinload(Impressora.local),
            selectinload(Leitura.tipo_impressao),
        )
        .where(
            and_(
                Leitura.mes_referencia == mes,
                Leitura.ano_referencia == ano,
            )
        )
    )
    leituras_atuais = (await db.execute(stmt_atual)).scalars().all()

    # Calcula mês anterior para obter a variação
    mes_ant = mes - 1 if mes > 1 else 12
    ano_ant = ano if mes > 1 else ano - 1

    stmt_ant = select(Leitura).where(
        and_(
            Leitura.mes_referencia == mes_ant,
            Leitura.ano_referencia == ano_ant,
        )
    )
    leituras_anteriores = {
        (l.impressora_num_serie, l.tipo_impressao_id): l
        for l in (await db.execute(stmt_ant)).scalars().all()
    }

    itens: List[RelatorioMensalItem] = []
    total_paginas = 0
    total_valor = Decimal("0.00")

    for leit in leituras_atuais:
        chave = (leit.impressora_num_serie, leit.tipo_impressao_id)
        leit_ant = leituras_anteriores.get(chave)
        contador_inicial = leit_ant.contador if leit_ant else 0
        paginas = max(0, leit.contador - contador_inicial)

        ti = leit.tipo_impressao
        dentro, exc, vf, ve, vt = _calcular_valor_impressao(
            paginas, ti.franquia, ti.valor_franquia, ti.valor_extra_franquia
        )

        itens.append(
            RelatorioMensalItem(
                impressora_num_serie=leit.impressora_num_serie,
                impressora_nome=leit.impressora.nome,
                setor=leit.impressora.local.setor,
                tipo_impressao=ti.descricao,
                mes=mes,
                ano=ano,
                contador_inicial=contador_inicial,
                contador_final=leit.contador,
                paginas_impressas=paginas,
                franquia=ti.franquia,
                paginas_dentro_franquia=dentro,
                paginas_excedente=exc,
                valor_franquia=vf,
                valor_excedente=ve,
                valor_total=vt,
            )
        )
        total_paginas += paginas
        total_valor += vt

    # Percentuais
    total_empenhado = sum(d.valor for d in contrato.documentos_contabeis)
    pct_orcamento = (
        float(total_valor / total_empenhado * 100) if total_empenhado > 0 else 0.0
    )

    hoje = date.today()
    dias_totais = (contrato.data_termino - contrato.data_inicio).days or 1
    dias_decorridos = max(0, (hoje - contrato.data_inicio).days)
    pct_tempo = min(100.0, dias_decorridos / dias_totais * 100)

    return RelatorioMensal(
        contrato_numero=contrato.numero,
        empresa_nome=contrato.empresa.nome,
        mes=mes,
        ano=ano,
        itens=itens,
        total_paginas=total_paginas,
        total_valor=total_valor,
        percentual_orcamento=round(pct_orcamento, 2),
        percentual_tempo=round(pct_tempo, 2),
    )


@router.get(
    "/total/{contrato_id}",
    response_model=RelatorioTotal,
    summary="Relatório total do contrato",
)
async def relatorio_total(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> RelatorioTotal:
    """
    Gera o relatório consolidado para toda a vigência do contrato.

    Inclui:
    - Total de páginas e valor por tipo de impressão
    - Total empenhado vs. consumido
    - Percentual de orçamento consumido
    - Percentual de tempo decorrido
    - Número de meses com leitura e impressoras ativas
    """
    contrato = await _obter_contrato(contrato_id, db)

    stmt = (
        select(Leitura)
        .options(selectinload(Leitura.tipo_impressao))
        .order_by(
            Leitura.impressora_num_serie,
            Leitura.tipo_impressao_id,
            Leitura.ano_referencia,
            Leitura.mes_referencia,
        )
    )
    todas_leituras = (await db.execute(stmt)).scalars().all()

    # Agrupa leituras por (impressora, tipo) para calcular variações mensais
    grupos: dict = {}
    for l in todas_leituras:
        chave = (l.impressora_num_serie, l.tipo_impressao_id)
        grupos.setdefault(chave, []).append(l)

    totais_por_tipo: dict[str, dict] = {}

    for (num_serie, tipo_id), leituras_ordenadas in grupos.items():
        for i, leit in enumerate(leituras_ordenadas):
            contador_anterior = leituras_ordenadas[i - 1].contador if i > 0 else 0
            paginas = max(0, leit.contador - contador_anterior)
            ti = leit.tipo_impressao
            _, _, _, _, vt = _calcular_valor_impressao(
                paginas, ti.franquia, ti.valor_franquia, ti.valor_extra_franquia
            )
            entrada = totais_por_tipo.setdefault(
                ti.descricao, {"paginas": 0, "valor": Decimal("0.00")}
            )
            entrada["paginas"] += paginas
            entrada["valor"] += vt

    itens = [
        RelatorioTotalItem(
            tipo_impressao=desc,
            total_paginas=dados["paginas"],
            total_valor=dados["valor"],
        )
        for desc, dados in totais_por_tipo.items()
    ]

    total_paginas = sum(i.total_paginas for i in itens)
    total_valor = sum(i.total_valor for i in itens)
    total_empenhado = sum(d.valor for d in contrato.documentos_contabeis)

    pct_orcamento = (
        float(total_valor / total_empenhado * 100) if total_empenhado > 0 else 0.0
    )

    hoje = date.today()
    dias_totais = max(1, (contrato.data_termino - contrato.data_inicio).days)
    dias_decorridos = max(0, min(dias_totais, (hoje - contrato.data_inicio).days))
    pct_tempo = dias_decorridos / dias_totais * 100

    meses_unicos = {(l.mes_referencia, l.ano_referencia) for l in todas_leituras}
    impressoras_ativas = len({l.impressora_num_serie for l in todas_leituras})

    return RelatorioTotal(
        contrato_numero=contrato.numero,
        empresa_nome=contrato.empresa.nome,
        data_inicio=contrato.data_inicio,
        data_termino=contrato.data_termino,
        numero_processo=contrato.numero_processo,
        itens=itens,
        total_geral_paginas=total_paginas,
        total_geral_valor=total_valor,
        total_empenhado=total_empenhado,
        percentual_orcamento_consumido=round(pct_orcamento, 2),
        percentual_tempo_decorrido=round(pct_tempo, 2),
        dias_decorridos=dias_decorridos,
        dias_totais=dias_totais,
        meses_com_leitura=len(meses_unicos),
        impressoras_ativas=impressoras_ativas,
    )


@router.get(
    "/evolucao/{contrato_id}",
    response_model=List[EvolucaoMensalItem],
    summary="Evolução mensal de consumo (para gráficos)",
)
async def evolucao_mensal(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> List[EvolucaoMensalItem]:
    """
    Retorna a série temporal de consumo mensal para geração de gráficos.

    Cada item representa um mês com o total de páginas e valor correspondente.
    """
    contrato = await _obter_contrato(contrato_id, db)

    stmt = (
        select(Leitura)
        .options(selectinload(Leitura.tipo_impressao))
        .order_by(Leitura.ano_referencia, Leitura.mes_referencia, Leitura.impressora_num_serie)
    )
    leituras = (await db.execute(stmt)).scalars().all()

    # Agrupa por (mes, ano, impressora, tipo) para calcular variações
    meses: dict = {}
    grupos: dict = {}
    for l in leituras:
        chave_grupo = (l.impressora_num_serie, l.tipo_impressao_id)
        grupos.setdefault(chave_grupo, []).append(l)

    for (num_serie, tipo_id), lista in grupos.items():
        for i, leit in enumerate(lista):
            anterior = lista[i - 1].contador if i > 0 else 0
            paginas = max(0, leit.contador - anterior)
            ti = leit.tipo_impressao
            _, _, _, _, vt = _calcular_valor_impressao(
                paginas, ti.franquia, ti.valor_franquia, ti.valor_extra_franquia
            )
            chave_mes = (leit.ano_referencia, leit.mes_referencia)
            entrada = meses.setdefault(
                chave_mes, {"paginas": 0, "valor": Decimal("0.00")}
            )
            entrada["paginas"] += paginas
            entrada["valor"] += vt

    return [
        EvolucaoMensalItem(
            mes=mes,
            ano=ano,
            label=f"{MESES_PT[mes]}/{ano}",
            total_paginas=dados["paginas"],
            total_valor=dados["valor"],
        )
        for (ano, mes), dados in sorted(meses.items())
    ]


@router.get(
    "/ranking/{contrato_id}",
    response_model=List[RankingImpressora],
    summary="Ranking de impressoras por volume de impressão",
)
async def ranking_impressoras(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> List[RankingImpressora]:
    """Retorna as impressoras ordenadas pelo volume total de páginas impressas."""
    await _obter_contrato(contrato_id, db)

    stmt = (
        select(Leitura)
        .options(
            selectinload(Leitura.impressora).selectinload(Impressora.local),
            selectinload(Leitura.tipo_impressao),
        )
        .order_by(Leitura.impressora_num_serie, Leitura.ano_referencia, Leitura.mes_referencia)
    )
    leituras = (await db.execute(stmt)).scalars().all()

    por_impressora: dict = {}
    grupos: dict = {}
    for l in leituras:
        grupos.setdefault((l.impressora_num_serie, l.tipo_impressao_id), []).append(l)

    for (num_serie, tipo_id), lista in grupos.items():
        for i, leit in enumerate(lista):
            anterior = lista[i - 1].contador if i > 0 else 0
            paginas = max(0, leit.contador - anterior)
            ti = leit.tipo_impressao
            _, _, _, _, vt = _calcular_valor_impressao(
                paginas, ti.franquia, ti.valor_franquia, ti.valor_extra_franquia
            )
            imp = leit.impressora
            entrada = por_impressora.setdefault(
                num_serie,
                {
                    "nome": imp.nome,
                    "setor": imp.local.setor,
                    "paginas": 0,
                    "valor": Decimal("0.00"),
                },
            )
            entrada["paginas"] += paginas
            entrada["valor"] += vt

    ranking = sorted(por_impressora.items(), key=lambda x: x[1]["paginas"], reverse=True)
    return [
        RankingImpressora(
            posicao=i + 1,
            num_serie=ns,
            nome=d["nome"],
            setor=d["setor"],
            total_paginas=d["paginas"],
            total_valor=d["valor"],
        )
        for i, (ns, d) in enumerate(ranking)
    ]


@router.get(
    "/snmp-teste/{num_serie}",
    summary="Testa conectividade SNMP de uma impressora",
)
async def testar_snmp(
    num_serie: str,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> dict:
    """
    Testa se a impressora está acessível via SNMP.

    Retorna a descrição do sistema (sysDescr) se acessível,
    ou detalhes do erro caso contrário.
    """
    imp = await db.get(Impressora, num_serie)
    if not imp:
        raise HTTPException(status_code=404, detail="Impressora não encontrada.")
    if not imp.ip:
        raise HTTPException(status_code=422, detail="Impressora sem IP configurado.")

    resultado = await testar_conectividade_snmp(imp.ip)
    return {"impressora": num_serie, "ip": imp.ip, **resultado}
