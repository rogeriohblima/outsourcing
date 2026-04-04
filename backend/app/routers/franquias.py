"""
routers/franquias.py — Gestão de franquias e tabelas de preço por contrato.

Endpoints:
  GET  /franquias/{contrato_id}              — Lista franquias do contrato
  POST /franquias/                           — Cria franquia (tipo + páginas + custo fixo)
  PUT  /franquias/{franquia_id}              — Atualiza franquia
  DELETE /franquias/{franquia_id}            — Remove franquia

  GET  /tabelas-preco/{contrato_id}          — Lista tabelas de preço (com histórico)
  POST /tabelas-preco/                       — Cria primeira tabela de preço
  POST /tabelas-preco/{contrato_id}/reajuste — Registra reajuste (fecha anterior, abre novo)
"""

from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import Contrato, FranquiaContrato, TabelaPreco, TipoImpressao
from app.schemas.schemas import (
    FranquiaContratoCreate,
    FranquiaContratoOut,
    FranquiaContratoUpdate,
    ReajustePrecoRequest,
    TabelaPrecoCreate,
    TabelaPrecoOut,
)

router = APIRouter(tags=["Franquias e Preços"])


# ── Franquias ─────────────────────────────────────────────────────────────────

@router.get("/franquias/{contrato_id}", response_model=List[FranquiaContratoOut],
            summary="Lista franquias do contrato")
async def listar_franquias(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> List[FranquiaContratoOut]:
    """
    Lista todas as franquias configuradas para o contrato.
    Cada tipo de impressão tem sua própria franquia (total de páginas + custo fixo mensal).
    """
    stmt = (
        select(FranquiaContrato)
        .where(FranquiaContrato.contrato_id == contrato_id)
        .options(selectinload(FranquiaContrato.tipo_impressao))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/franquias/", response_model=FranquiaContratoOut,
             status_code=status.HTTP_201_CREATED,
             summary="Configura franquia para um tipo de impressão no contrato")
async def criar_franquia(
    body: FranquiaContratoCreate,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> FranquiaContratoOut:
    """
    Cria a configuração de franquia para um tipo de impressão em um contrato.

    - **paginas_franquia**: total de páginas contratadas para toda a vigência
    - **valor_mensal_franquia**: custo fixo mensal pago independente do uso

    Nota: os valores por página (dentro/fora da franquia) são definidos
    separadamente em Tabelas de Preço, permitindo histórico de reajustes.
    """
    if not await db.get(Contrato, body.contrato_id):
        raise HTTPException(status_code=404, detail="Contrato não encontrado.")
    if not await db.get(TipoImpressao, body.tipo_impressao_id):
        raise HTTPException(status_code=404, detail="Tipo de impressão não encontrado.")

    # Verifica duplicidade
    existing = await db.execute(
        select(FranquiaContrato).where(
            and_(
                FranquiaContrato.contrato_id == body.contrato_id,
                FranquiaContrato.tipo_impressao_id == body.tipo_impressao_id,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Já existe franquia para este tipo de impressão neste contrato.",
        )

    franquia = FranquiaContrato(**body.model_dump())
    db.add(franquia)
    await db.flush()

    stmt = (
        select(FranquiaContrato)
        .where(FranquiaContrato.id == franquia.id)
        .options(selectinload(FranquiaContrato.tipo_impressao))
    )
    return (await db.execute(stmt)).scalar_one()


@router.put("/franquias/{franquia_id}", response_model=FranquiaContratoOut,
            summary="Atualiza franquia")
async def atualizar_franquia(
    franquia_id: int,
    body: FranquiaContratoUpdate,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> FranquiaContratoOut:
    """
    Atualiza a configuração de franquia.
    Atenção: alterar paginas_franquia afeta todos os cálculos retroativos.
    """
    franquia = await db.get(FranquiaContrato, franquia_id)
    if not franquia:
        raise HTTPException(status_code=404, detail="Franquia não encontrada.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(franquia, k, v)
    await db.flush()

    stmt = (
        select(FranquiaContrato)
        .where(FranquiaContrato.id == franquia_id)
        .options(selectinload(FranquiaContrato.tipo_impressao))
    )
    return (await db.execute(stmt)).scalar_one()


@router.delete("/franquias/{franquia_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Remove franquia")
async def remover_franquia(
    franquia_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> None:
    franquia = await db.get(FranquiaContrato, franquia_id)
    if not franquia:
        raise HTTPException(status_code=404, detail="Franquia não encontrada.")
    await db.delete(franquia)
    await db.flush()


# ── Tabelas de Preço ──────────────────────────────────────────────────────────

@router.get("/tabelas-preco/{contrato_id}", response_model=List[TabelaPrecoOut],
            summary="Lista tabelas de preço do contrato (com histórico)")
async def listar_tabelas_preco(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> List[TabelaPrecoOut]:
    """
    Lista todas as tabelas de preço do contrato, incluindo o histórico de reajustes.

    Registros com vigente_ate=None são os preços atualmente vigentes.
    Registros com vigente_ate preenchido são históricos (nunca alterados).
    """
    stmt = (
        select(TabelaPreco)
        .where(TabelaPreco.contrato_id == contrato_id)
        .options(selectinload(TabelaPreco.tipo_impressao))
        .order_by(TabelaPreco.tipo_impressao_id, TabelaPreco.vigente_de.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


@router.post("/tabelas-preco/", response_model=TabelaPrecoOut,
             status_code=status.HTTP_201_CREATED,
             summary="Cria tabela de preço inicial")
async def criar_tabela_preco(
    body: TabelaPrecoCreate,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> TabelaPrecoOut:
    """
    Cria a tabela de preço inicial para um tipo de impressão em um contrato.

    Use este endpoint apenas para a configuração inicial.
    Para reajustes posteriores, use POST /tabelas-preco/{contrato_id}/reajuste.
    """
    if not await db.get(Contrato, body.contrato_id):
        raise HTTPException(status_code=404, detail="Contrato não encontrado.")
    if not await db.get(TipoImpressao, body.tipo_impressao_id):
        raise HTTPException(status_code=404, detail="Tipo de impressão não encontrado.")

    # Verifica se já existe tabela vigente (sem data de fim)
    existing = await db.execute(
        select(TabelaPreco).where(
            and_(
                TabelaPreco.contrato_id == body.contrato_id,
                TabelaPreco.tipo_impressao_id == body.tipo_impressao_id,
                TabelaPreco.vigente_ate.is_(None),
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe tabela de preço vigente para este tipo. "
                "Para reajustar, use POST /tabelas-preco/{contrato_id}/reajuste."
            ),
        )

    tabela = TabelaPreco(**body.model_dump(), vigente_ate=None)
    db.add(tabela)
    await db.flush()

    stmt = (
        select(TabelaPreco)
        .where(TabelaPreco.id == tabela.id)
        .options(selectinload(TabelaPreco.tipo_impressao))
    )
    return (await db.execute(stmt)).scalar_one()


@router.post("/tabelas-preco/{contrato_id}/reajuste", response_model=TabelaPrecoOut,
             status_code=status.HTTP_201_CREATED,
             summary="Registra reajuste de preços")
async def reajustar_preco(
    contrato_id: int,
    body: ReajustePrecoRequest,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> TabelaPrecoOut:
    """
    Registra um reajuste de preços para um tipo de impressão.

    Fluxo:
      1. Fecha o preço atual (define vigente_ate = vigente_de_novo - 1 dia)
      2. Cria novo registro com os novos valores a partir de vigente_de

    Os cálculos de períodos anteriores ao reajuste continuam usando o preço
    antigo (histórico imutável), garantindo rastreabilidade completa.

    Restrições:
      - vigente_de deve ser posterior à data de início do preço anterior
      - Não é permitido alterar registros com vigente_ate preenchido
    """
    if not await db.get(Contrato, contrato_id):
        raise HTTPException(status_code=404, detail="Contrato não encontrado.")

    # Busca o preço vigente atual
    stmt = select(TabelaPreco).where(
        and_(
            TabelaPreco.contrato_id == contrato_id,
            TabelaPreco.tipo_impressao_id == body.tipo_impressao_id,
            TabelaPreco.vigente_ate.is_(None),
        )
    )
    vigente_atual = (await db.execute(stmt)).scalar_one_or_none()

    if not vigente_atual:
        raise HTTPException(
            status_code=404,
            detail=(
                "Nenhum preço vigente encontrado para este tipo de impressão. "
                "Crie o preço inicial com POST /tabelas-preco/."
            ),
        )

    if body.vigente_de <= vigente_atual.vigente_de:
        raise HTTPException(
            status_code=422,
            detail=(
                f"A data de início do reajuste ({body.vigente_de}) deve ser "
                f"posterior ao início do preço atual ({vigente_atual.vigente_de})."
            ),
        )

    # Fecha o preço atual (um dia antes do novo)
    vigente_atual.vigente_ate = body.vigente_de - timedelta(days=1)

    # Cria o novo preço
    novo = TabelaPreco(
        contrato_id=contrato_id,
        tipo_impressao_id=body.tipo_impressao_id,
        valor_dentro_franquia=body.valor_dentro_franquia,
        valor_fora_franquia=body.valor_fora_franquia,
        vigente_de=body.vigente_de,
        vigente_ate=None,  # preço atual
    )
    db.add(novo)
    await db.flush()

    stmt = (
        select(TabelaPreco)
        .where(TabelaPreco.id == novo.id)
        .options(selectinload(TabelaPreco.tipo_impressao))
    )
    return (await db.execute(stmt)).scalar_one()
