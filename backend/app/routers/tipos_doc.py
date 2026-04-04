"""
routers/tipos_doc.py — CRUD de Tipos de Documento Contábil.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import TipoDoc
from app.schemas.schemas import TipoDocCreate, TipoDocOut, TipoDocUpdate

router = APIRouter(prefix="/tipos-doc", tags=["Tipos de Documento"])


@router.get("/", response_model=List[TipoDocOut])
async def listar(db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    result = await db.execute(select(TipoDoc).order_by(TipoDoc.nome))
    return list(result.scalars().all())


@router.post("/", response_model=TipoDocOut, status_code=status.HTTP_201_CREATED)
async def criar(body: TipoDocCreate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    t = TipoDoc(**body.model_dump())
    db.add(t)
    await db.flush()
    return t


@router.get("/{tipo_id}", response_model=TipoDocOut)
async def obter(tipo_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    t = await db.get(TipoDoc, tipo_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tipo de documento não encontrado.")
    return t


@router.patch("/{tipo_id}", response_model=TipoDocOut)
async def atualizar(tipo_id: int, body: TipoDocUpdate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    t = await db.get(TipoDoc, tipo_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tipo de documento não encontrado.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    return t


@router.delete("/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(tipo_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    t = await db.get(TipoDoc, tipo_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tipo de documento não encontrado.")
    await db.delete(t)
    await db.flush()
