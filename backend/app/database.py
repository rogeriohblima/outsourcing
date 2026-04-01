"""
database.py — Configuração do banco de dados assíncrono.

Suporta PostgreSQL (produção via asyncpg) e SQLite (desenvolvimento
via aiosqlite). A URL do banco é lida das configurações da aplicação.

Padrão utilizado: SQLAlchemy 2.0 com AsyncSession e DeclarativeBase.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# ── Engine Assíncrona ─────────────────────────────────────────────────────────
# connect_args somente necessário para SQLite (evita erros de thread)
_connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,           # Loga SQL gerado quando em modo debug
    connect_args=_connect_args,
    pool_pre_ping=True,            # Verifica conexão antes de usar do pool
)

# ── Session Factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,        # Evita lazy-load após commit em contexto async
    autoflush=False,
    autocommit=False,
)


# ── Base Declarativa ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """
    Classe base para todos os modelos ORM do sistema.

    Todos os modelos devem herdar desta classe para que o Alembic
    detecte automaticamente as migrações necessárias.
    """
    pass


# ── Dependency Injection ──────────────────────────────────────────────────────
async def get_db() -> AsyncSession:  # type: ignore[return]
    """
    Dependency do FastAPI que fornece uma sessão de banco de dados
    assíncrona por requisição HTTP.

    Uso nos routers:
        async def meu_endpoint(db: AsyncSession = Depends(get_db)):
            ...

    A sessão é automaticamente fechada ao final da requisição,
    com rollback em caso de exceção.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_all_tables() -> None:
    """
    Cria todas as tabelas do banco de dados.

    Utilizado apenas em desenvolvimento/testes com SQLite.
    Em produção, utilize sempre o Alembic (`alembic upgrade head`).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """
    Remove todas as tabelas. Usado exclusivamente em testes.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
