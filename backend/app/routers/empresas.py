"""
routers/empresas.py — CRUD de Empresas.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import Empresa
from app.schemas.schemas import EmpresaCreate, EmpresaOut, EmpresaUpdate

router = APIRouter(prefix="/empresas", tags=["Empresas"])


@router.get("/", response_model=List[EmpresaOut])
async def listar(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    result = await db.execute(select(Empresa).offset(skip).limit(limit).order_by(Empresa.nome))
    return list(result.scalars().all())


@router.post("/", response_model=EmpresaOut, status_code=status.HTTP_201_CREATED)
async def criar(body: EmpresaCreate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    if await db.get(Empresa, body.cnpj):
        raise HTTPException(status_code=409, detail="CNPJ já cadastrado.")
    e = Empresa(**body.model_dump())
    db.add(e)
    await db.flush()
    return e


@router.get("/{cnpj}", response_model=EmpresaOut)
async def obter(cnpj: str, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    e = await db.get(Empresa, cnpj)
    if not e:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return e


@router.patch("/{cnpj}", response_model=EmpresaOut)
async def atualizar(cnpj: str, body: EmpresaUpdate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    e = await db.get(Empresa, cnpj)
    if not e:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(e, k, v)
    return e


@router.delete("/{cnpj}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(cnpj: str, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    e = await db.get(Empresa, cnpj)
    if not e:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    await db.delete(e)
    await db.flush()
