"""Adiciona coluna valor_estimado na tabela contratos

Revision ID: 002
Revises: 001
Create Date: 2025-01-02 00:00:00.000000
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona valor_estimado (Numeric 14,2) na tabela contratos."""
    op.add_column(
        "contratos",
        sa.Column(
            "valor_estimado",
            sa.Numeric(14, 2),
            nullable=False,
            server_default="0",   # valor padrao para registros existentes
        ),
    )


def downgrade() -> None:
    """Remove a coluna valor_estimado da tabela contratos."""
    op.drop_column("contratos", "valor_estimado")