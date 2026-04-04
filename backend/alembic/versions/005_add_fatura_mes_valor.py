"""Adiciona mes_referencia, ano_referencia e valor na tabela faturas

Revision ID: 005
Revises: 004
Create Date: 2025-01-05 00:00:00.000000
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("faturas") as batch_op:
        batch_op.add_column(sa.Column("mes_referencia", sa.Integer(), nullable=False, server_default="1"))
        batch_op.add_column(sa.Column("ano_referencia", sa.Integer(), nullable=False, server_default="2025"))
        batch_op.add_column(sa.Column("valor", sa.Numeric(14, 2), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("faturas") as batch_op:
        batch_op.drop_column("valor")
        batch_op.drop_column("ano_referencia")
        batch_op.drop_column("mes_referencia")
