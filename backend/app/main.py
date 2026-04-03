"""
main.py — Ponto de entrada da aplicação FastAPI.

Registra todos os routers, configura CORS, eventos de startup/shutdown
e define metadados da API (título, versão, descrição).

Para iniciar:
    uvicorn app.main:app --reload
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth.router import router as auth_router
from app.config import get_settings
from app.database import create_all_tables
from app.routers.comissoes import router as comissoes_router
from app.routers.contratos import router as contratos_router
from app.routers.documentos_contabeis import router as docs_contabeis_router
from app.routers.empresas import router as empresas_router
from app.routers.faturas import router as faturas_router
from app.routers.impressoras import router as impressoras_router
from app.routers.leituras import router as leituras_router
from app.routers.locais_impressora import router as locais_router
from app.routers.membros import router as membros_router
from app.routers.relatorios import router as relatorios_router
from app.routers.tipos_doc import router as tipos_doc_router
from app.routers.tipos_impressao import router as tipos_impressao_router
from app.routers.tipos_impressora import router as tipos_impressora_router

logging.basicConfig(
    level=logging.DEBUG if get_settings().DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gerencia o ciclo de vida da aplicação.

    Startup: cria tabelas automaticamente em SQLite (desenvolvimento).
             Em PostgreSQL, utilize sempre `alembic upgrade head`.
    Shutdown: recursos de banco são fechados pelo próprio SQLAlchemy.
    """
    logger.info("Iniciando %s (env=%s)", settings.APP_NAME, settings.APP_ENV)

    if settings.is_sqlite:
        logger.info("SQLite detectado — criando tabelas automaticamente.")
        await create_all_tables()

    # Garante que o diretório de uploads existe
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    yield

    logger.info("Encerrando aplicação.")


# ── Aplicação FastAPI ─────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "API REST para gerenciamento de contratos de impressoras "
        "de Organizações Militares da Aeronáutica. "
        "Autenticação via Active Directory (JWT). "
        "Leitura de contadores via SNMP."
    ),
    contact={"name": "SETIC / Organização Militar"},
    lifespan=lifespan,
    # Desativa docs em produção se desejado
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

PREFIX = "/api/v1"

app.include_router(auth_router,             prefix=PREFIX)
app.include_router(membros_router,          prefix=PREFIX)
app.include_router(empresas_router,         prefix=PREFIX)
app.include_router(comissoes_router,        prefix=PREFIX)
app.include_router(contratos_router,        prefix=PREFIX)
app.include_router(faturas_router,          prefix=PREFIX)
app.include_router(docs_contabeis_router,   prefix=PREFIX)
app.include_router(tipos_doc_router,        prefix=PREFIX)
app.include_router(tipos_impressora_router, prefix=PREFIX)
app.include_router(locais_router,           prefix=PREFIX)
app.include_router(impressoras_router,      prefix=PREFIX)
app.include_router(tipos_impressao_router,  prefix=PREFIX)
app.include_router(leituras_router,         prefix=PREFIX)
app.include_router(relatorios_router,       prefix=PREFIX)

# ── Arquivos estáticos (uploads) ──────────────────────────────────────────────

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR, check_dir=False), name="uploads")



# ── Rota raiz ─────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    """Redireciona a raiz (/) para a documentacao interativa da API."""
    return RedirectResponse(url="/docs")


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Sistema"], summary="Verificação de saúde da API")
async def health() -> dict:
    """Retorna status da API. Usado por balanceadores de carga e monitoramento."""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}