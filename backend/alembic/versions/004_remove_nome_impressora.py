"""Remove coluna nome da tabela impressoras

Revision ID: 004
Revises: 003
Create Date: 2025-01-04 00:00:00.000000

O nome da impressora agora e derivado do ModeloImpressora (fabricante + modelo).
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove a coluna nome da tabela impressoras."""
    # SQLite nao suporta DROP COLUMN diretamente em versoes antigas.
    # Para PostgreSQL basta: op.drop_column("impressoras", "nome")
    # Para compatibilidade com SQLite, usamos batch_alter_table.
    with op.batch_alter_table("impressoras") as batch_op:
        batch_op.drop_column("nome")


def downgrade() -> None:
    """Restaura a coluna nome (valor padrao vazio)."""
    with op.batch_alter_table("impressoras") as batch_op:
        batch_op.add_column(
            sa.Column("nome", sa.String(200), nullable=False, server_default="")
        )
