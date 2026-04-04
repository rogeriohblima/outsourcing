"""
routers/impressoras.py — CRUD de Impressoras.

Inclui endpoint para leitura SNMP ad-hoc (sem persistir),
útil para testar a conectividade antes de salvar.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import Impressora, LocalImpressora, ModeloImpressora, TipoImpressora
from app.schemas.schemas import (
    ImpressoraCreate,
    ImpressoraOut,
    ImpressoraUpdate,
    SNMPResultado,
)
from app.services.snmp_service import ler_contador_snmp

router = APIRouter(prefix="/impressoras", tags=["Impressoras"])

_LOAD = [
    selectinload(Impressora.tipo),
    selectinload(Impressora.local),
    selectinload(Impressora.modelo),
]


async def _get_or_404(num_serie: str, db: AsyncSession) -> Impressora:
    stmt = select(Impressora).options(*_LOAD).where(Impressora.num_serie == num_serie)
    imp = (await db.execute(stmt)).scalar_one_or_none()
    if not imp:
        raise HTTPException(status_code=404, detail="Impressora não encontrada.")
    return imp


@router.get("/", response_model=List[ImpressoraOut], summary="Lista impressoras")
async def listar(
    ativa: bool | None = Query(None, description="Filtra por status ativo/inativo"),
    local_id: int | None = Query(None),
    skip: int = 0,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
):
    stmt = select(Impressora).options(*_LOAD).offset(skip).limit(limit).order_by(Impressora.num_serie)
    if ativa is not None:
        stmt = stmt.where(Impressora.ativa == ativa)
    if local_id is not None:
        stmt = stmt.where(Impressora.local_id == local_id)
    return list((await db.execute(stmt)).scalars().all())


@router.post("/", response_model=ImpressoraOut, status_code=status.HTTP_201_CREATED)
async def criar(body: ImpressoraCreate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    if await db.get(Impressora, body.num_serie):
        raise HTTPException(status_code=409, detail="Número de série já cadastrado.")
    if not await db.get(TipoImpressora, body.tipo_id):
        raise HTTPException(status_code=404, detail="Tipo de impressora não encontrado.")
    if not await db.get(LocalImpressora, body.local_id):
        raise HTTPException(status_code=404, detail="Local de impressora não encontrado.")
    imp = Impressora(**body.model_dump())
    db.add(imp)
    await db.flush()
    return await _get_or_404(imp.num_serie, db)


@router.get("/{num_serie}", response_model=ImpressoraOut)
async def obter(num_serie: str, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    return await _get_or_404(num_serie, db)


@router.patch("/{num_serie}", response_model=ImpressoraOut)
async def atualizar(num_serie: str, body: ImpressoraUpdate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    imp = await db.get(Impressora, num_serie)
    if not imp:
        raise HTTPException(status_code=404, detail="Impressora não encontrada.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(imp, k, v)
    await db.flush()
    return await _get_or_404(num_serie, db)


@router.delete("/{num_serie}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(num_serie: str, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    imp = await db.get(Impressora, num_serie)
    if not imp:
        raise HTTPException(status_code=404, detail="Impressora não encontrada.")
    await db.delete(imp)
    await db.flush()


@router.get(
    "/{num_serie}/snmp",
    response_model=SNMPResultado,
    summary="Lê contador SNMP sem persistir",
    description="Consulta o contador atual da impressora via SNMP sem salvar no banco. Útil para testes.",
)
async def ler_snmp(
    num_serie: str,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> SNMPResultado:
    imp = await _get_or_404(num_serie, db)
    if not imp.ip:
        raise HTTPException(status_code=422, detail="Impressora sem IP configurado.")
    resultado = await ler_contador_snmp(imp.ip)
    return SNMPResultado(
        sucesso=resultado.sucesso,
        contador=resultado.contador,
        oid_usado=resultado.oid_usado,
        erro=resultado.erro,
    )
