"""
routers/membros.py — CRUD de Membros da comissão.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import Membro
from app.schemas.schemas import MembroCreate, MembroOut, MembroUpdate

router = APIRouter(prefix="/membros", tags=["Membros"])


@router.get("/", response_model=List[MembroOut], summary="Lista membros")
async def listar(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    result = await db.execute(select(Membro).offset(skip).limit(limit).order_by(Membro.nome))
    return list(result.scalars().all())


@router.post("/", response_model=MembroOut, status_code=status.HTTP_201_CREATED, summary="Cria membro")
async def criar(body: MembroCreate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    if await db.get(Membro, body.cpf):
        raise HTTPException(status_code=409, detail="CPF já cadastrado.")
    m = Membro(**body.model_dump())
    db.add(m)
    await db.flush()
    return m


@router.get("/{cpf}", response_model=MembroOut, summary="Detalhe do membro")
async def obter(cpf: str, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    m = await db.get(Membro, cpf)
    if not m:
        raise HTTPException(status_code=404, detail="Membro não encontrado.")
    return m


@router.patch("/{cpf}", response_model=MembroOut, summary="Atualiza membro")
async def atualizar(cpf: str, body: MembroUpdate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    m = await db.get(Membro, cpf)
    if not m:
        raise HTTPException(status_code=404, detail="Membro não encontrado.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    return m


@router.delete("/{cpf}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove membro")
async def remover(cpf: str, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    m = await db.get(Membro, cpf)
    if not m:
        raise HTTPException(status_code=404, detail="Membro não encontrado.")
    await db.delete(m)
    await db.flush()
