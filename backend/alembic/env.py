"""
alembic/env.py — Configuração do Alembic para migrações de banco de dados.

Usa a URL síncrona (SYNC_DATABASE_URL) definida no .env para
executar migrações. Importa os modelos para que o Alembic detecte
automaticamente as alterações de schema (autogenerate).
"""

import sys
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Garante que o diretório raiz do backend está no PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Importa todos os modelos para que o Alembic os detecte via metadata
from app.database import Base
from app.models import models  # noqa: F401 — importa para registrar os modelos

from app.config import get_settings

settings_app = get_settings()

# Lê o arquivo alembic.ini
config = context.config

# Sobrescreve a URL com a variável de ambiente (síncrona)
config.set_main_option("sqlalchemy.url", settings_app.SYNC_DATABASE_URL)

# Configura logging conforme alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata de todos os modelos para autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Modo offline: gera o SQL sem se conectar ao banco.
    Útil para revisar as migrações antes de aplicar.
    Execute com: alembic upgrade head --sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Modo online: conecta ao banco e aplica as migrações diretamente.
    Execute com: alembic upgrade head
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
