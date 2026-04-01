"""
tests/conftest.py — Fixtures compartilhadas entre todos os testes.

Este arquivo é carregado automaticamente pelo pytest antes de qualquer teste.

Estratégia de banco de dados para testes:
- Usa SQLite em memória (':memory:') para isolamento total entre testes.
- Cada função de teste recebe uma sessão nova com rollback automático,
  garantindo que os dados de um teste não afetam outro.
- O token JWT de teste é gerado com credenciais fixas (sem AD).

Fixtures disponíveis:
  - engine_test      : engine SQLAlchemy assíncrono em memória
  - db               : sessão AsyncSession por teste (rollback ao final)
  - client           : AsyncClient do FastAPI com banco e auth configurados
  - auth_headers     : headers com Bearer token para requisições autenticadas
  - membro_fixture   : Membro pré-criado no banco
  - empresa_fixture  : Empresa pré-criada no banco
  - tipo_impressora  : TipoImpressora pré-criada
  - local_impressora : LocalImpressora pré-criada
  - impressora_fixture: Impressora pré-criada (depende dos acima)
  - tipo_impressao   : TipoImpressao pré-criada
"""

import asyncio
from datetime import datetime
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.service import criar_token_acesso
from app.database import Base, get_db
from app.main import app
from app.models.models import (
    Empresa,
    Impressora,
    LocalImpressora,
    Membro,
    TipoImpressao,
    TipoImpressora,
)

# ── Configuração do Engine de Teste ──────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """
    Loop de eventos compartilhado para toda a sessão de testes.
    Necessário para fixtures de escopo 'session' com asyncio.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine_test():
    """
    Cria o engine SQLite em memória e as tabelas uma única vez por sessão.
    Descarta tudo ao final da sessão.
    """
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(engine_test) -> AsyncGenerator[AsyncSession, None]:
    """
    Sessão de banco de dados isolada por teste.

    Cada teste recebe uma sessão dentro de uma transação que é revertida
    (rollback) ao final, garantindo isolamento completo entre testes.
    """
    SessionLocal = async_sessionmaker(bind=engine_test, expire_on_commit=False)

    async with engine_test.begin() as conn:
        async with SessionLocal(bind=conn) as session:
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP assíncrono do FastAPI configurado para testes.

    Substitui a dependency `get_db` pela sessão de teste,
    garantindo que as requisições usem o banco em memória.
    """
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict:
    """
    Headers de autenticação com Bearer token JWT válido para testes.

    Cria um token com usuário 'test_user' sem validar no AD.
    """
    token = criar_token_acesso(
        username="test_user",
        nome="Usuário de Teste",
        grupos=["GRP_TESTE"],
    )
    return {"Authorization": f"Bearer {token}"}


# ── Fixtures de Entidades ─────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def membro_fixture(db: AsyncSession) -> Membro:
    """Cria e persiste um Membro para uso nos testes."""
    membro = Membro(cpf="123.456.789-00", nome="Cap Silva")
    db.add(membro)
    await db.flush()
    return membro


@pytest_asyncio.fixture
async def empresa_fixture(db: AsyncSession) -> Empresa:
    """Cria e persiste uma Empresa para uso nos testes."""
    empresa = Empresa(cnpj="12.345.678/0001-90", nome="Empresa Teste LTDA")
    db.add(empresa)
    await db.flush()
    return empresa


@pytest_asyncio.fixture
async def tipo_impressora(db: AsyncSession) -> TipoImpressora:
    """Cria e persiste um TipoImpressora para uso nos testes."""
    tipo = TipoImpressora(tipo="Laser Monocromático")
    db.add(tipo)
    await db.flush()
    return tipo


@pytest_asyncio.fixture
async def local_impressora(db: AsyncSession) -> LocalImpressora:
    """Cria e persiste um LocalImpressora para uso nos testes."""
    local = LocalImpressora(setor="SETIC", descricao="Sala do servidor")
    db.add(local)
    await db.flush()
    return local


@pytest_asyncio.fixture
async def impressora_fixture(
    db: AsyncSession,
    tipo_impressora: TipoImpressora,
    local_impressora: LocalImpressora,
) -> Impressora:
    """
    Cria e persiste uma Impressora completa para uso nos testes.
    Depende das fixtures tipo_impressora e local_impressora.
    """
    imp = Impressora(
        num_serie="SN-TEST-001",
        nome="HP LaserJet Test",
        tipo_id=tipo_impressora.id,
        local_id=local_impressora.id,
        ip="192.168.1.100",
        ativa=True,
    )
    db.add(imp)
    await db.flush()
    return imp


@pytest_asyncio.fixture
async def tipo_impressao(db: AsyncSession) -> TipoImpressao:
    """Cria e persiste um TipoImpressao com valores de franquia para testes."""
    ti = TipoImpressao(
        descricao="Preto e Branco A4",
        franquia=5000,
        valor_franquia="500.00",
        valor_extra_franquia="0.05",
    )
    db.add(ti)
    await db.flush()
    return ti
