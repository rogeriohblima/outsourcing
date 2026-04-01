"""
routers/comissoes.py — CRUD de Comissões com upload de documento.

O documento oficial da comissão (PDF) pode ser enviado via multipart/form-data.
"""
import os
import shutil
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserInfo
from app.config import get_settings
from app.database import get_db
from app.models.models import Comissao, Membro
from app.schemas.schemas import ComissaoCreate, ComissaoOut, ComissaoUpdate

router = APIRouter(prefix="/comissoes", tags=["Comissões"])
settings = get_settings()

_LOAD = [
    selectinload(Comissao.presidente),
    selectinload(Comissao.fiscais),
]


async def _get_or_404(comissao_id: int, db: AsyncSession) -> Comissao:
    stmt = select(Comissao).options(*_LOAD).where(Comissao.id == comissao_id)
    c = (await db.execute(stmt)).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Comissão não encontrada.")
    return c


@router.get("/", response_model=List[ComissaoOut])
async def listar(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    stmt = select(Comissao).options(*_LOAD).offset(skip).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


@router.post("/", response_model=ComissaoOut, status_code=status.HTTP_201_CREATED)
async def criar(body: ComissaoCreate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    """Cria comissão. Para upload do documento, use o endpoint PATCH /{id}/documento."""
    presidente = await db.get(Membro, body.presidente_cpf)
    if not presidente:
        raise HTTPException(status_code=404, detail="Presidente (Membro) não encontrado.")

    fiscais = []
    for cpf in body.fiscais_cpf:
        fiscal = await db.get(Membro, cpf)
        if not fiscal:
            raise HTTPException(status_code=404, detail=f"Fiscal CPF {cpf} não encontrado.")
        fiscais.append(fiscal)

    dados = body.model_dump(exclude={"fiscais_cpf"})
    c = Comissao(**dados)
    c.fiscais = fiscais
    db.add(c)
    await db.flush()
    return await _get_or_404(c.id, db)


@router.get("/{comissao_id}", response_model=ComissaoOut)
async def obter(comissao_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    return await _get_or_404(comissao_id, db)


@router.patch("/{comissao_id}", response_model=ComissaoOut)
async def atualizar(comissao_id: int, body: ComissaoUpdate, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    c = await _get_or_404(comissao_id, db)
    dados = body.model_dump(exclude_unset=True, exclude={"fiscais_cpf"})
    for k, v in dados.items():
        setattr(c, k, v)

    if body.fiscais_cpf is not None:
        fiscais = []
        for cpf in body.fiscais_cpf:
            fiscal = await db.get(Membro, cpf)
            if not fiscal:
                raise HTTPException(status_code=404, detail=f"Fiscal CPF {cpf} não encontrado.")
            fiscais.append(fiscal)
        c.fiscais = fiscais

    await db.flush()
    return await _get_or_404(comissao_id, db)


@router.post("/{comissao_id}/documento", response_model=ComissaoOut, summary="Upload do documento PDF")
async def upload_documento(
    comissao_id: int,
    arquivo: UploadFile = File(..., description="Arquivo PDF do ato de designação"),
    db: AsyncSession = Depends(get_db),
    _: UserInfo = Depends(get_current_user),
):
    """
    Faz upload do documento PDF da comissão (BI, portaria de designação, etc.).
    O arquivo é salvo no diretório configurado em UPLOAD_DIR.
    """
    c = await _get_or_404(comissao_id, db)

    if not arquivo.content_type or "pdf" not in arquivo.content_type.lower():
        raise HTTPException(status_code=422, detail="Somente arquivos PDF são aceitos.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    nome_arquivo = f"comissao_{comissao_id}_{arquivo.filename}"
    caminho = os.path.join(settings.UPLOAD_DIR, nome_arquivo)

    with open(caminho, "wb") as f:
        shutil.copyfileobj(arquivo.file, f)

    c.documento_path = caminho
    await db.flush()
    return await _get_or_404(comissao_id, db)


@router.delete("/{comissao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(comissao_id: int, db: AsyncSession = Depends(get_db), _: UserInfo = Depends(get_current_user)):
    c = await db.get(Comissao, comissao_id)
    if not c:
        raise HTTPException(status_code=404, detail="Comissão não encontrada.")
    await db.delete(c)
