"""
routers/tipos_impressora.py — CRUD de Tipos de Impressora.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import TipoImpressora
from app.schemas.schemas import TipoImpressoraCreate, TipoImpressoraOut, TipoImpressoraUpdate

router = APIRouter(prefix="/tipos-impressora", tags=["Tipos de Impressora"])


@router.get("/", response_model=List[TipoImpressoraOut])
async def listar(db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    result = await db.execute(select(TipoImpressora).order_by(TipoImpressora.tipo))
    return list(result.scalars().all())


@router.post("/", response_model=TipoImpressoraOut, status_code=status.HTTP_201_CREATED)
async def criar(body: TipoImpressoraCreate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    t = TipoImpressora(**body.model_dump())
    db.add(t)
    await db.flush()
    return t


@router.get("/{tipo_id}", response_model=TipoImpressoraOut)
async def obter(tipo_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    t = await db.get(TipoImpressora, tipo_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tipo de impressora não encontrado.")
    return t


@router.patch("/{tipo_id}", response_model=TipoImpressoraOut)
async def atualizar(tipo_id: int, body: TipoImpressoraUpdate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    t = await db.get(TipoImpressora, tipo_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tipo de impressora não encontrado.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    return t


@router.delete("/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(tipo_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    t = await db.get(TipoImpressora, tipo_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tipo de impressora não encontrado.")
    await db.delete(t)
    await db.flush()
