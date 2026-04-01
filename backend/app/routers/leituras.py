"""
routers/leituras.py — CRUD de leituras de contadores.

Endpoints:
  GET    /leituras/              — Lista leituras (com filtros)
  POST   /leituras/              — Cria leitura manual
  POST   /leituras/snmp          — Dispara leitura automática via SNMP
  GET    /leituras/{id}          — Detalhe de uma leitura
  PATCH  /leituras/{id}          — Atualiza leitura
  DELETE /leituras/{id}          — Remove leitura
  GET    /leituras/impressora/{num_serie} — Leituras por impressora
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import Impressora, Leitura
from app.schemas.schemas import (
    LeituraCreate,
    LeituraOut,
    LeituraSNMPRequest,
    LeituraUpdate,
    SNMPResultado,
)
from app.services.snmp_service import ler_contador_snmp

router = APIRouter(prefix="/leituras", tags=["Leituras"])

# Carrega relacionamentos aninhados com uma única query
_LOAD_OPTIONS = [
    selectinload(Leitura.impressora).selectinload(Impressora.tipo),
    selectinload(Leitura.impressora).selectinload(Impressora.local),
    selectinload(Leitura.tipo_impressao),
]


@router.get("/", response_model=List[LeituraOut], summary="Lista leituras")
async def listar_leituras(
    impressora_num_serie: Optional[str] = Query(None),
    mes_referencia: Optional[int] = Query(None, ge=1, le=12),
    ano_referencia: Optional[int] = Query(None, ge=2000),
    manual: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> List[LeituraOut]:
    """Lista leituras com filtros opcionais por impressora, mês/ano e origem."""
    stmt = select(Leitura).options(*_LOAD_OPTIONS).order_by(
        Leitura.ano_referencia.desc(), Leitura.mes_referencia.desc()
    )
    if impressora_num_serie:
        stmt = stmt.where(Leitura.impressora_num_serie == impressora_num_serie)
    if mes_referencia is not None:
        stmt = stmt.where(Leitura.mes_referencia == mes_referencia)
    if ano_referencia is not None:
        stmt = stmt.where(Leitura.ano_referencia == ano_referencia)
    if manual is not None:
        stmt = stmt.where(Leitura.manual == manual)
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post(
    "/",
    response_model=LeituraOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria leitura manual",
)
async def criar_leitura(
    body: LeituraCreate,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> LeituraOut:
    """
    Cria uma leitura de contador inserida manualmente pelo fiscal.

    Use este endpoint quando a leitura SNMP não for possível.
    O campo 'manual' será definido como True automaticamente se não informado.
    """
    # Valida se a impressora existe
    imp = await db.get(Impressora, body.impressora_num_serie)
    if not imp:
        raise HTTPException(status_code=404, detail="Impressora não encontrada.")

    leitura = Leitura(**body.model_dump())
    leitura.manual = True  # Garantia: criação via API sempre é manual
    db.add(leitura)
    await db.flush()

    stmt = select(Leitura).options(*_LOAD_OPTIONS).where(Leitura.id == leitura.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.post(
    "/snmp",
    response_model=LeituraOut,
    status_code=status.HTTP_201_CREATED,
    summary="Leitura automática via SNMP",
    description=(
        "Consulta o contador da impressora via SNMP e salva o resultado. "
        "Se a leitura SNMP falhar, retorna HTTP 422 com detalhes do erro, "
        "e o usuário deve usar o endpoint de leitura manual."
    ),
)
async def leitura_snmp(
    body: LeituraSNMPRequest,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> LeituraOut:
    """
    Dispara leitura automática do contador via SNMP.

    Requer que a impressora tenha um IP configurado e que o agente
    SNMP esteja ativo e acessível pelo servidor da aplicação.
    """
    imp = await db.get(Impressora, body.impressora_num_serie)
    if not imp:
        raise HTTPException(status_code=404, detail="Impressora não encontrada.")

    if not imp.ip:
        raise HTTPException(
            status_code=422,
            detail="Impressora não possui IP configurado. Use leitura manual.",
        )

    resultado = await ler_contador_snmp(imp.ip)

    if not resultado.sucesso or resultado.contador is None:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Leitura SNMP falhou: {resultado.erro}. "
                "Realize o lançamento manual do contador."
            ),
        )

    leitura = Leitura(
        impressora_num_serie=body.impressora_num_serie,
        tipo_impressao_id=body.tipo_impressao_id,
        contador=resultado.contador,
        data=date.today(),
        mes_referencia=body.mes_referencia,
        ano_referencia=body.ano_referencia,
        manual=False,
        observacao=f"SNMP automático — OID: {resultado.oid_usado}",
    )
    db.add(leitura)
    await db.flush()

    stmt = select(Leitura).options(*_LOAD_OPTIONS).where(Leitura.id == leitura.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get(
    "/impressora/{num_serie}",
    response_model=List[LeituraOut],
    summary="Leituras por impressora",
)
async def leituras_por_impressora(
    num_serie: str,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> List[LeituraOut]:
    """Retorna todas as leituras de uma impressora específica."""
    stmt = (
        select(Leitura)
        .options(*_LOAD_OPTIONS)
        .where(Leitura.impressora_num_serie == num_serie)
        .order_by(Leitura.ano_referencia.desc(), Leitura.mes_referencia.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{leitura_id}", response_model=LeituraOut, summary="Detalhe de leitura")
async def obter_leitura(
    leitura_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> LeituraOut:
    stmt = select(Leitura).options(*_LOAD_OPTIONS).where(Leitura.id == leitura_id)
    result = await db.execute(stmt)
    leitura = result.scalar_one_or_none()
    if not leitura:
        raise HTTPException(status_code=404, detail="Leitura não encontrada.")
    return leitura


@router.patch("/{leitura_id}", response_model=LeituraOut, summary="Atualiza leitura")
async def atualizar_leitura(
    leitura_id: int,
    body: LeituraUpdate,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> LeituraOut:
    """Atualiza campos de uma leitura existente (somente campos enviados)."""
    leitura = await db.get(Leitura, leitura_id)
    if not leitura:
        raise HTTPException(status_code=404, detail="Leitura não encontrada.")

    for campo, valor in body.model_dump(exclude_unset=True).items():
        setattr(leitura, campo, valor)

    await db.flush()
    stmt = select(Leitura).options(*_LOAD_OPTIONS).where(Leitura.id == leitura_id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.delete(
    "/{leitura_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove leitura",
)
async def remover_leitura(
    leitura_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
) -> None:
    leitura = await db.get(Leitura, leitura_id)
    if not leitura:
        raise HTTPException(status_code=404, detail="Leitura não encontrada.")
    await db.delete(leitura)
