"""
tests/conftest.py — Fixtures compartilhadas entre todos os testes.

Estratégia de banco de dados:
  - SQLite em memória para isolamento total entre testes.
  - Cada teste recebe uma sessão com rollback automático ao final.
  - Todos os db.delete() nos routers têm db.flush() — garantindo que o DELETE
    é efetivado dentro da mesma transação antes do GET seguinte.

Fixtures disponíveis:
  - db                : AsyncSession isolada por teste (rollback ao final)
  - client            : AsyncClient com banco de teste injetado
  - auth_headers      : Bearer token JWT válido para testes
  - membro_fixture    : Membro pré-criado
  - empresa_fixture   : Empresa pré-criada
  - tipo_impressora   : TipoImpressora pré-criada
  - local_impressora  : LocalImpressora pré-criada
  - modelo_impressora : ModeloImpressora pré-criada
  - impressora_fixture: Impressora pré-criada (depende dos 3 acima)
  - tipo_impressao    : TipoImpressao pré-criada (sem campos de franquia)
  - contrato_base     : Contrato simples com empresa e comissão
"""

import os

# Define variáveis de ambiente ANTES de qualquer import da aplicação.
# Isso evita que o Settings() seja instanciado sem as configurações de teste,
# o que causaria ValidationError do pydantic.
os.environ.setdefault("DATABASE_URL",      "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SYNC_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY",        "chave-de-teste-nao-usar-em-producao-12345678")
os.environ.setdefault("APP_ENV",           "testing")
os.environ.setdefault("DEBUG",             "false")
os.environ.setdefault("AD_SERVER",         "127.0.0.1")
os.environ.setdefault("AD_DOMAIN",         "teste.local")
os.environ.setdefault("AD_BASE_DN",        "DC=teste,DC=local")
os.environ.setdefault("UPLOAD_DIR",        "/tmp/sci_test_uploads")


import asyncio
from datetime import date
from decimal import Decimal
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.service import criar_token_acesso
from app.database import Base, get_db
from app.main import app
from app.models.models import (
    Comissao,
    Contrato,
    Empresa,
    FranquiaContrato,
    Impressora,
    LocalImpressora,
    Membro,
    ModeloImpressora,
    TabelaPreco,
    TipoDoc,
    TipoImpressao,
    TipoImpressora,
)

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Loop de eventos compartilhado para toda a sessão de testes."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine_test():
    """Engine SQLite em memória — criado uma vez por sessão de testes."""
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
    Sessão assíncrona isolada por teste com rollback automático.

    Todos os dados criados durante o teste são descartados ao final,
    garantindo isolamento total entre testes.
    """
    SessionLocal = async_sessionmaker(bind=engine_test, expire_on_commit=False)
    async with engine_test.begin() as conn:
        async with SessionLocal(bind=conn) as session:
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    AsyncClient do FastAPI com banco de dados de teste injetado.

    Substitui get_db pela sessão de teste para que todas as requisições
    operem no banco em memória.
    """
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict:
    """Bearer token JWT válido para autenticação nos testes (sem AD)."""
    token = criar_token_acesso(
        username="test_user",
        nome="Usuário de Teste",
        grupos=["GRP_TESTE"],
    )
    return {"Authorization": f"Bearer {token}"}


# ── Fixtures de Entidades Básicas ─────────────────────────────────────────────

@pytest_asyncio.fixture
async def membro_fixture(db: AsyncSession) -> Membro:
    """Membro com CPF único para uso como presidente de comissão."""
    m = Membro(cpf="123.456.789-00", nome="Cap Silva")
    db.add(m)
    await db.flush()
    return m


@pytest_asyncio.fixture
async def empresa_fixture(db: AsyncSession) -> Empresa:
    """Empresa contratada para uso em contratos de teste."""
    e = Empresa(cnpj="12.345.678-0001-90", nome="Empresa Teste LTDA")
    db.add(e)
    await db.flush()
    return e


@pytest_asyncio.fixture
async def tipo_impressora(db: AsyncSession) -> TipoImpressora:
    """Tipo de impressora laser monocromático."""
    t = TipoImpressora(tipo="Laser Monocromático")
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
async def local_impressora(db: AsyncSession) -> LocalImpressora:
    """Local de impressora no setor SETIC."""
    l = LocalImpressora(setor="SETIC", descricao="Sala do servidor")
    db.add(l)
    await db.flush()
    return l


@pytest_asyncio.fixture
async def modelo_impressora(db: AsyncSession) -> ModeloImpressora:
    """Modelo HP LaserJet Pro M404n para uso em impressoras de teste."""
    m = ModeloImpressora(
        fabricante="HP",
        modelo="LaserJet Pro M404n",
        descricao="Laser monocromatico A4, 38 ppm",
    )
    db.add(m)
    await db.flush()
    return m


@pytest_asyncio.fixture
async def impressora_fixture(
    db: AsyncSession,
    tipo_impressora: TipoImpressora,
    local_impressora: LocalImpressora,
    modelo_impressora: ModeloImpressora,
) -> Impressora:
    """
    Impressora completa com IP para testes de leituras e SNMP.
    Depende das fixtures tipo_impressora, local_impressora e modelo_impressora.
    """
    imp = Impressora(
        num_serie="SN-TEST-001",
        modelo_id=modelo_impressora.id,
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
    """
    TipoImpressao 'Preto e Branco A4'.

    Nota: a partir da nova lógica de franquia, TipoImpressao contém apenas
    a descrição. Os valores de franquia e preço ficam em FranquiaContrato
    e TabelaPreco vinculados ao contrato específico.
    """
    ti = TipoImpressao(descricao="Preto e Branco A4")
    db.add(ti)
    await db.flush()
    return ti


@pytest_asyncio.fixture
async def contrato_base(
    db: AsyncSession,
    empresa_fixture: Empresa,
    membro_fixture: Membro,
) -> Contrato:
    """
    Contrato de teste completo com comissão, franquia e tabela de preços.

    Inclui:
      - Comissão com presidente (membro_fixture)
      - Contrato de 1 ano (Jan/2025 a Dez/2025)
      - Tipo de impressão P&B A4
      - Franquia: 60.000 páginas totais, R$ 500/mês de custo fixo
      - Tabela de preço: R$ 0,04/pág dentro, R$ 0,08/pág fora
    """
    comissao = Comissao(
        presidente_cpf=membro_fixture.cpf,
        documento_numero="BI-TEST-001",
        documento_data=date(2025, 1, 1),
    )
    db.add(comissao)
    await db.flush()

    contrato = Contrato(
        numero="CT-TEST-001",
        empresa_cnpj=empresa_fixture.cnpj,
        data_inicio=date(2025, 1, 1),
        data_termino=date(2025, 12, 31),
        comissao_id=comissao.id,
        numero_processo="NUP-TEST-001",
        valor_estimado=Decimal("10000.00"),
    )
    db.add(contrato)
    await db.flush()

    tipo_doc = TipoDoc(nome="NE-TEST")
    db.add(tipo_doc)
    await db.flush()

    return contrato
