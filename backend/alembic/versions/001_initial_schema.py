"""Schema inicial — criação de todas as tabelas do sistema.

Revision ID: 001
Revises: 
Create Date: 2025-01-01 00:00:00.000000

Esta migração cria a estrutura completa do banco de dados para o
Sistema de Contratos de Impressoras (SCI) da Organização Militar da Aeronáutica.

Tabelas criadas (em ordem de dependência):
  1. membros
  2. comissoes
  3. comissao_fiscais (N:N)
  4. empresas
  5. contratos
  6. faturas
  7. tipos_doc
  8. documentos_contabeis
  9. tipos_impressora
  10. locais_impressora
  11. impressoras
  12. tipos_impressao
  13. leituras
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# ── Identificadores da revisão ────────────────────────────────────────────────

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Upgrade: cria todas as tabelas ────────────────────────────────────────────

def upgrade() -> None:

    # ── membros ───────────────────────────────────────────────────────────────
    op.create_table(
        "membros",
        sa.Column("cpf",        sa.String(14),  primary_key=True, nullable=False),
        sa.Column("nome",       sa.String(200), nullable=False),
        sa.Column("criado_em",  sa.DateTime(),  server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_index("ix_membros_cpf", "membros", ["cpf"])

    # ── comissoes ─────────────────────────────────────────────────────────────
    op.create_table(
        "comissoes",
        sa.Column("id",               sa.Integer(),    primary_key=True, autoincrement=True),
        sa.Column("presidente_cpf",   sa.String(14),   sa.ForeignKey("membros.cpf"), nullable=False),
        sa.Column("documento_numero", sa.String(100),  nullable=False),
        sa.Column("documento_data",   sa.Date(),       nullable=False),
        sa.Column("documento_path",   sa.String(500),  nullable=True),
        sa.Column("criado_em",        sa.DateTime(),   server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )

    # ── comissao_fiscais (N:N) ────────────────────────────────────────────────
    op.create_table(
        "comissao_fiscais",
        sa.Column("comissao_id", sa.Integer(),   sa.ForeignKey("comissoes.id",  ondelete="CASCADE"), primary_key=True),
        sa.Column("membro_cpf",  sa.String(14),  sa.ForeignKey("membros.cpf",   ondelete="CASCADE"), primary_key=True),
    )

    # ── empresas ──────────────────────────────────────────────────────────────
    op.create_table(
        "empresas",
        sa.Column("cnpj",       sa.String(18),  primary_key=True, nullable=False),
        sa.Column("nome",       sa.String(300), nullable=False),
        sa.Column("criado_em",  sa.DateTime(),  server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_index("ix_empresas_cnpj", "empresas", ["cnpj"])

    # ── contratos ─────────────────────────────────────────────────────────────
    op.create_table(
        "contratos",
        sa.Column("id",              sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column("numero",          sa.String(50),  nullable=False, unique=True),
        sa.Column("empresa_cnpj",    sa.String(18),  sa.ForeignKey("empresas.cnpj"), nullable=False),
        sa.Column("data_inicio",     sa.Date(),      nullable=False),
        sa.Column("data_termino",    sa.Date(),      nullable=False),
        sa.Column("comissao_id",     sa.Integer(),   sa.ForeignKey("comissoes.id"), nullable=False),
        sa.Column("numero_processo", sa.String(100), nullable=False),
        sa.Column("criado_em",       sa.DateTime(),  server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_index("ix_contratos_numero", "contratos", ["numero"])

    # ── faturas ───────────────────────────────────────────────────────────────
    op.create_table(
        "faturas",
        sa.Column("id",          sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column("numero",      sa.String(100), nullable=False),
        sa.Column("data",        sa.Date(),      nullable=False),
        sa.Column("contrato_id", sa.Integer(),   sa.ForeignKey("contratos.id"), nullable=False),
        sa.Column("criado_em",   sa.DateTime(),  server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_index("ix_faturas_numero", "faturas", ["numero"])

    # ── tipos_doc ─────────────────────────────────────────────────────────────
    op.create_table(
        "tipos_doc",
        sa.Column("id",   sa.Integer(),    primary_key=True, autoincrement=True),
        sa.Column("nome", sa.String(100),  nullable=False, unique=True),
    )

    # ── documentos_contabeis ──────────────────────────────────────────────────
    op.create_table(
        "documentos_contabeis",
        sa.Column("id",               sa.Integer(),      primary_key=True, autoincrement=True),
        sa.Column("numero",           sa.String(100),    nullable=False),
        sa.Column("tipo_documento_id",sa.Integer(),      sa.ForeignKey("tipos_doc.id"),  nullable=False),
        sa.Column("contrato_id",      sa.Integer(),      sa.ForeignKey("contratos.id"), nullable=False),
        sa.Column("valor",            sa.Numeric(14, 2), nullable=False),
        sa.Column("criado_em",        sa.DateTime(),     server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_index("ix_documentos_contabeis_numero", "documentos_contabeis", ["numero"])

    # ── tipos_impressora ──────────────────────────────────────────────────────
    op.create_table(
        "tipos_impressora",
        sa.Column("id",   sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column("tipo", sa.String(100), nullable=False, unique=True),
    )

    # ── locais_impressora ─────────────────────────────────────────────────────
    op.create_table(
        "locais_impressora",
        sa.Column("id",        sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column("setor",     sa.String(100), nullable=False),
        sa.Column("descricao", sa.String(300), nullable=False),
    )

    # ── impressoras ───────────────────────────────────────────────────────────
    op.create_table(
        "impressoras",
        sa.Column("num_serie", sa.String(100), primary_key=True, nullable=False),
        sa.Column("nome",      sa.String(200), nullable=False),
        sa.Column("tipo_id",   sa.Integer(),   sa.ForeignKey("tipos_impressora.id"), nullable=False),
        sa.Column("local_id",  sa.Integer(),   sa.ForeignKey("locais_impressora.id"), nullable=False),
        sa.Column("ip",        sa.String(45),  nullable=True),
        sa.Column("ativa",     sa.Boolean(),   nullable=False, default=True),
        sa.Column("criado_em", sa.DateTime(),  server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_index("ix_impressoras_num_serie", "impressoras", ["num_serie"])

    # ── tipos_impressao ───────────────────────────────────────────────────────
    op.create_table(
        "tipos_impressao",
        sa.Column("id",                   sa.Integer(),      primary_key=True, autoincrement=True),
        sa.Column("descricao",            sa.String(200),    nullable=False, unique=True),
        sa.Column("franquia",             sa.Integer(),      nullable=False, default=0),
        sa.Column("valor_franquia",       sa.Numeric(14, 2), nullable=False, default=0),
        sa.Column("valor_extra_franquia", sa.Numeric(14, 2), nullable=False, default=0),
    )

    # ── leituras ──────────────────────────────────────────────────────────────
    op.create_table(
        "leituras",
        sa.Column("id",                   sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column("impressora_num_serie", sa.String(100), sa.ForeignKey("impressoras.num_serie"), nullable=False),
        sa.Column("tipo_impressao_id",    sa.Integer(),   sa.ForeignKey("tipos_impressao.id"),   nullable=False),
        sa.Column("contador",             sa.Integer(),   nullable=False),
        sa.Column("data",                 sa.Date(),      nullable=False),
        sa.Column("mes_referencia",       sa.Integer(),   nullable=False),
        sa.Column("ano_referencia",       sa.Integer(),   nullable=False),
        sa.Column("manual",               sa.Boolean(),   nullable=False, default=False),
        sa.Column("observacao",           sa.Text(),      nullable=True),
        sa.Column("criado_em",            sa.DateTime(),  server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_index("ix_leituras_impressora_num_serie", "leituras", ["impressora_num_serie"])

    # ── Seed: tipos de documento padrão ──────────────────────────────────────
    op.execute(
        "INSERT INTO tipos_doc (nome) VALUES ('NE'), ('OB'), ('RP'), ('NS')"
    )


# ── Downgrade: remove todas as tabelas (ordem inversa de FK) ──────────────────

def downgrade() -> None:
    op.drop_table("leituras")
    op.drop_table("tipos_impressao")
    op.drop_table("impressoras")
    op.drop_table("locais_impressora")
    op.drop_table("tipos_impressora")
    op.drop_table("documentos_contabeis")
    op.drop_table("tipos_doc")
    op.drop_table("faturas")
    op.drop_table("contratos")
    op.drop_table("empresas")
    op.drop_table("comissao_fiscais")
    op.drop_table("comissoes")
    op.drop_table("membros")
