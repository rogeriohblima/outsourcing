"""
routers/modelos_impressora.py — CRUD de Modelos de Impressora.

Permite cadastrar os modelos comerciais de impressoras (ex: HP LaserJet Pro M404n)
para serem selecionados no cadastro de impressoras físicas.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import ModeloImpressora
from app.schemas.schemas import (
    ModeloImpressoraCreate,
    ModeloImpressoraOut,
    ModeloImpressoraUpdate,
)

router = APIRouter(prefix="/modelos-impressora", tags=["Modelos de Impressora"])


@router.get("/", response_model=List[ModeloImpressoraOut], summary="Lista modelos")
async def listar(
    fabricante: Optional[str] = Query(None, description="Filtra por fabricante"),
    skip: int = 0,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> List[ModeloImpressoraOut]:
    """Lista todos os modelos de impressora, com filtro opcional por fabricante."""
    stmt = (
        select(ModeloImpressora)
        .order_by(ModeloImpressora.fabricante, ModeloImpressora.modelo)
        .offset(skip)
        .limit(limit)
    )
    if fabricante:
        stmt = stmt.where(ModeloImpressora.fabricante.ilike(f"%{fabricante}%"))
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post(
    "/",
    response_model=ModeloImpressoraOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria modelo",
)
async def criar(
    body: ModeloImpressoraCreate,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> ModeloImpressoraOut:
    """Cadastra um novo modelo de impressora."""
    m = ModeloImpressora(**body.model_dump())
    db.add(m)
    await db.flush()
    return m


@router.get("/{modelo_id}", response_model=ModeloImpressoraOut, summary="Detalhe do modelo")
async def obter(
    modelo_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> ModeloImpressoraOut:
    m = await db.get(ModeloImpressora, modelo_id)
    if not m:
        raise HTTPException(status_code=404, detail="Modelo nao encontrado.")
    return m


@router.patch("/{modelo_id}", response_model=ModeloImpressoraOut, summary="Atualiza modelo")
async def atualizar(
    modelo_id: int,
    body: ModeloImpressoraUpdate,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> ModeloImpressoraOut:
    m = await db.get(ModeloImpressora, modelo_id)
    if not m:
        raise HTTPException(status_code=404, detail="Modelo nao encontrado.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    return m


@router.delete("/{modelo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove modelo")
async def remover(
    modelo_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> None:
    m = await db.get(ModeloImpressora, modelo_id)
    if not m:
        raise HTTPException(status_code=404, detail="Modelo nao encontrado.")
    await db.delete(m)
