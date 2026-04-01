"""
routers/documentos_contabeis.py — CRUD de Documentos Contábeis (NE, OB, etc.).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.database import get_db
from app.models.models import Contrato, DocumentoContabil, TipoDoc
from app.schemas.schemas import DocumentoContabilCreate, DocumentoContabilOut, DocumentoContabilUpdate

router = APIRouter(prefix="/documentos-contabeis", tags=["Documentos Contábeis"])

_LOAD = [
    selectinload(DocumentoContabil.tipo_documento),
    selectinload(DocumentoContabil.contrato).selectinload(Contrato.empresa),
]


async def _get_or_404(doc_id: int, db: AsyncSession) -> DocumentoContabil:
    stmt = select(DocumentoContabil).options(*_LOAD).where(DocumentoContabil.id == doc_id)
    d = (await db.execute(stmt)).scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Documento contábil não encontrado.")
    return d


@router.get("/", response_model=List[DocumentoContabilOut], summary="Lista documentos contábeis")
async def listar(
    contrato_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
):
    stmt = select(DocumentoContabil).options(*_LOAD).offset(skip).limit(limit)
    if contrato_id is not None:
        stmt = stmt.where(DocumentoContabil.contrato_id == contrato_id)
    return list((await db.execute(stmt)).scalars().all())


@router.post("/", response_model=DocumentoContabilOut, status_code=status.HTTP_201_CREATED)
async def criar(body: DocumentoContabilCreate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    if not await db.get(Contrato, body.contrato_id):
        raise HTTPException(status_code=404, detail="Contrato não encontrado.")
    if not await db.get(TipoDoc, body.tipo_documento_id):
        raise HTTPException(status_code=404, detail="Tipo de documento não encontrado.")
    d = DocumentoContabil(**body.model_dump())
    db.add(d)
    await db.flush()
    return await _get_or_404(d.id, db)


@router.get("/{doc_id}", response_model=DocumentoContabilOut)
async def obter(doc_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    return await _get_or_404(doc_id, db)


@router.patch("/{doc_id}", response_model=DocumentoContabilOut)
async def atualizar(doc_id: int, body: DocumentoContabilUpdate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    d = await db.get(DocumentoContabil, doc_id)
    if not d:
        raise HTTPException(status_code=404, detail="Documento contábil não encontrado.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(d, k, v)
    await db.flush()
    return await _get_or_404(doc_id, db)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(doc_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    d = await db.get(DocumentoContabil, doc_id)
    if not d:
        raise HTTPException(status_code=404, detail="Documento contábil não encontrado.")
    await db.delete(d)
