"""
routers/tipos_impressao.py — CRUD de Tipos de Impressão (com franquia).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import TipoImpressao
from app.schemas.schemas import TipoImpressaoCreate, TipoImpressaoOut, TipoImpressaoUpdate

router = APIRouter(prefix="/tipos-impressao", tags=["Tipos de Impressão"])


@router.get("/", response_model=List[TipoImpressaoOut])
async def listar(db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    result = await db.execute(select(TipoImpressao).order_by(TipoImpressao.descricao))
    return list(result.scalars().all())


@router.post("/", response_model=TipoImpressaoOut, status_code=status.HTTP_201_CREATED)
async def criar(body: TipoImpressaoCreate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    t = TipoImpressao(**body.model_dump())
    db.add(t)
    await db.flush()
    return t


@router.get("/{tipo_id}", response_model=TipoImpressaoOut)
async def obter(tipo_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    t = await db.get(TipoImpressao, tipo_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tipo de impressão não encontrado.")
    return t


@router.patch("/{tipo_id}", response_model=TipoImpressaoOut)
async def atualizar(tipo_id: int, body: TipoImpressaoUpdate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    t = await db.get(TipoImpressao, tipo_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tipo de impressão não encontrado.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    return t


@router.delete("/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(tipo_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    t = await db.get(TipoImpressao, tipo_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tipo de impressão não encontrado.")
    await db.delete(t)
