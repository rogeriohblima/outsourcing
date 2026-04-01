"""
routers/contratos.py — CRUD de Contratos.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import Comissao, Contrato, Empresa
from app.schemas.schemas import ContratoCreate, ContratoOut, ContratoUpdate

router = APIRouter(prefix="/contratos", tags=["Contratos"])

_LOAD = [
    selectinload(Contrato.empresa),
    selectinload(Contrato.comissao).selectinload(Comissao.presidente),
    selectinload(Contrato.comissao).selectinload(Comissao.fiscais),
]


async def _get_or_404(contrato_id: int, db: AsyncSession) -> Contrato:
    stmt = select(Contrato).options(*_LOAD).where(Contrato.id == contrato_id)
    c = (await db.execute(stmt)).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Contrato não encontrado.")
    return c


@router.get("/", response_model=List[ContratoOut])
async def listar(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    stmt = select(Contrato).options(*_LOAD).offset(skip).limit(limit).order_by(Contrato.numero)
    return list((await db.execute(stmt)).scalars().all())


@router.post("/", response_model=ContratoOut, status_code=status.HTTP_201_CREATED)
async def criar(body: ContratoCreate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    empresa = await db.get(Empresa, body.empresa_cnpj)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    comissao = await db.get(Comissao, body.comissao_id)
    if not comissao:
        raise HTTPException(status_code=404, detail="Comissão não encontrada.")

    c = Contrato(**body.model_dump())
    db.add(c)
    await db.flush()
    return await _get_or_404(c.id, db)


@router.get("/{contrato_id}", response_model=ContratoOut)
async def obter(contrato_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    return await _get_or_404(contrato_id, db)


@router.patch("/{contrato_id}", response_model=ContratoOut)
async def atualizar(contrato_id: int, body: ContratoUpdate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    c = await db.get(Contrato, contrato_id)
    if not c:
        raise HTTPException(status_code=404, detail="Contrato não encontrado.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    await db.flush()
    return await _get_or_404(contrato_id, db)


@router.delete("/{contrato_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(contrato_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    c = await db.get(Contrato, contrato_id)
    if not c:
        raise HTTPException(status_code=404, detail="Contrato não encontrado.")
    await db.delete(c)
