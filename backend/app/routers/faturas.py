"""
routers/faturas.py — CRUD de Faturas vinculadas a contratos.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import Contrato, Fatura
from app.schemas.schemas import FaturaCreate, FaturaOut, FaturaUpdate

router = APIRouter(prefix="/faturas", tags=["Faturas"])

_LOAD = [
    selectinload(Fatura.contrato).selectinload(Contrato.empresa),
]


async def _get_or_404(fatura_id: int, db: AsyncSession) -> Fatura:
    stmt = select(Fatura).options(*_LOAD).where(Fatura.id == fatura_id)
    f = (await db.execute(stmt)).scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=404, detail="Fatura não encontrada.")
    return f


@router.get("/", response_model=List[FaturaOut], summary="Lista faturas")
async def listar(
    contrato_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
):
    stmt = select(Fatura).options(*_LOAD).offset(skip).limit(limit).order_by(Fatura.data.desc())
    if contrato_id is not None:
        stmt = stmt.where(Fatura.contrato_id == contrato_id)
    return list((await db.execute(stmt)).scalars().all())


@router.post("/", response_model=FaturaOut, status_code=status.HTTP_201_CREATED)
async def criar(body: FaturaCreate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    contrato = await db.get(Contrato, body.contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado.")
    f = Fatura(**body.model_dump())
    db.add(f)
    await db.flush()
    return await _get_or_404(f.id, db)


@router.get("/{fatura_id}", response_model=FaturaOut)
async def obter(fatura_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    return await _get_or_404(fatura_id, db)


@router.patch("/{fatura_id}", response_model=FaturaOut)
async def atualizar(fatura_id: int, body: FaturaUpdate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    f = await db.get(Fatura, fatura_id)
    if not f:
        raise HTTPException(status_code=404, detail="Fatura não encontrada.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(f, k, v)
    await db.flush()
    return await _get_or_404(fatura_id, db)


@router.delete("/{fatura_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(fatura_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    f = await db.get(Fatura, fatura_id)
    if not f:
        raise HTTPException(status_code=404, detail="Fatura não encontrada.")
    await db.delete(f)
    await db.flush()
