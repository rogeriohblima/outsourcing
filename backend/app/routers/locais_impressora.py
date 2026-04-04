"""
routers/locais_impressora.py — CRUD de Locais de Impressora.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import LocalImpressora
from app.schemas.schemas import LocalImpressoraCreate, LocalImpressoraOut, LocalImpressoraUpdate

router = APIRouter(prefix="/locais-impressora", tags=["Locais de Impressora"])


@router.get("/", response_model=List[LocalImpressoraOut])
async def listar(db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    result = await db.execute(select(LocalImpressora).order_by(LocalImpressora.setor))
    return list(result.scalars().all())


@router.post("/", response_model=LocalImpressoraOut, status_code=status.HTTP_201_CREATED)
async def criar(body: LocalImpressoraCreate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    loc = LocalImpressora(**body.model_dump())
    db.add(loc)
    await db.flush()
    return loc


@router.get("/{local_id}", response_model=LocalImpressoraOut)
async def obter(local_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    loc = await db.get(LocalImpressora, local_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Local não encontrado.")
    return loc


@router.patch("/{local_id}", response_model=LocalImpressoraOut)
async def atualizar(local_id: int, body: LocalImpressoraUpdate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    loc = await db.get(LocalImpressora, local_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Local não encontrado.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(loc, k, v)
    return loc


@router.delete("/{local_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(local_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    loc = await db.get(LocalImpressora, local_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Local não encontrado.")
    await db.delete(loc)
    await db.flush()
