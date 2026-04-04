"""Adiciona tabela modelos_impressora e coluna modelo_id em impressoras

Revision ID: 003
Revises: 002
Create Date: 2025-01-03 00:00:00.000000
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Cria tabela modelos_impressora
    op.create_table(
        "modelos_impressora",
        sa.Column("id",         sa.Integer(),    primary_key=True, autoincrement=True),
        sa.Column("fabricante", sa.String(100),  nullable=False),
        sa.Column("modelo",     sa.String(200),  nullable=False),
        sa.Column("descricao",  sa.String(500),  nullable=True),
    )

    # Adiciona coluna modelo_id na tabela impressoras (nullable — campo opcional)
    op.add_column(
        "impressoras",
        sa.Column(
            "modelo_id",
            sa.Integer(),
            sa.ForeignKey("modelos_impressora.id"),
            nullable=True,
        ),
    )

    # Popula com alguns modelos comuns para facilitar o inicio do uso
    op.execute("""
        INSERT INTO modelos_impressora (fabricante, modelo, descricao) VALUES
        ('HP',     'LaserJet Pro M404n',       'Laser monocromatico A4, 38 ppm'),
        ('HP',     'LaserJet Pro MFP M428fdw', 'Multifuncional laser mono A4, 38 ppm'),
        ('HP',     'Color LaserJet Pro M454dw','Laser colorido A4, 28 ppm'),
        ('Xerox',  'VersaLink B405',            'Multifuncional laser mono A4, 47 ppm'),
        ('Xerox',  'VersaLink C405',            'Multifuncional laser color A4, 35 ppm'),
        ('Ricoh',  'IM 430F',                   'Multifuncional laser mono A4, 43 ppm'),
        ('Ricoh',  'IM C300',                   'Multifuncional laser color A4, 30 ppm'),
        ('Canon',  'imageCLASS MF445dw',        'Multifuncional laser mono A4, 40 ppm'),
        ('Canon',  'imageCLASS MF644Cdw',       'Multifuncional laser color A4, 22 ppm'),
        ('Lexmark','MB2650adwe',                 'Multifuncional laser mono A4, 50 ppm'),
        ('Brother','MFC-L5900DW',               'Multifuncional laser mono A4, 40 ppm'),
        ('Brother','MFC-L8900CDW',              'Multifuncional laser color A4, 33 ppm')
    """)


def downgrade() -> None:
    op.drop_column("impressoras", "modelo_id")
    op.drop_table("modelos_impressora")
