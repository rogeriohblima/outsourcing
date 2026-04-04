"""Schema completo v2 — inclui franquias, tabelas de preco e leitura por contrato

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

Esta migração cria toda a estrutura de banco de dados do SCI, incluindo:
  - Entidades base: membros, empresas, comissoes, contratos
  - Franquia por contrato e histórico de preços (nova lógica)
  - Impressoras com modelo
  - Leituras vinculadas ao contrato
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table("membros",
        sa.Column("cpf",       sa.String(14),  primary_key=True),
        sa.Column("nome",      sa.String(200), nullable=False),
        sa.Column("criado_em", sa.DateTime(),  server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )

    op.create_table("comissoes",
        sa.Column("id",               sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column("presidente_cpf",   sa.String(14),  sa.ForeignKey("membros.cpf"), nullable=False),
        sa.Column("documento_numero", sa.String(100), nullable=False),
        sa.Column("documento_data",   sa.Date(),      nullable=False),
        sa.Column("documento_path",   sa.String(500), nullable=True),
        sa.Column("criado_em",        sa.DateTime(),  server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )

    op.create_table("comissao_fiscais",
        sa.Column("comissao_id", sa.Integer(),  sa.ForeignKey("comissoes.id",  ondelete="CASCADE"), primary_key=True),
        sa.Column("membro_cpf",  sa.String(14), sa.ForeignKey("membros.cpf",   ondelete="CASCADE"), primary_key=True),
    )

    op.create_table("empresas",
        sa.Column("cnpj",      sa.String(18),  primary_key=True),
        sa.Column("nome",      sa.String(300), nullable=False),
        sa.Column("criado_em", sa.DateTime(),  server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )

    op.create_table("contratos",
        sa.Column("id",              sa.Integer(),      primary_key=True, autoincrement=True),
        sa.Column("numero",          sa.String(50),     nullable=False, unique=True),
        sa.Column("empresa_cnpj",    sa.String(18),     sa.ForeignKey("empresas.cnpj"), nullable=False),
        sa.Column("data_inicio",     sa.Date(),         nullable=False),
        sa.Column("data_termino",    sa.Date(),         nullable=False),
        sa.Column("comissao_id",     sa.Integer(),      sa.ForeignKey("comissoes.id"), nullable=False),
        sa.Column("numero_processo", sa.String(100),    nullable=False),
        sa.Column("valor_estimado",  sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("criado_em",       sa.DateTime(),     server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )

    op.create_table("faturas",
        sa.Column("id",             sa.Integer(),      primary_key=True, autoincrement=True),
        sa.Column("numero",         sa.String(100),    nullable=False),
        sa.Column("data",           sa.Date(),         nullable=False),
        sa.Column("mes_referencia", sa.Integer(),      nullable=False),
        sa.Column("ano_referencia", sa.Integer(),      nullable=False),
        sa.Column("valor",          sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("contrato_id",    sa.Integer(),      sa.ForeignKey("contratos.id"), nullable=False),
        sa.Column("criado_em",      sa.DateTime(),     server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )

    op.create_table("tipos_doc",
        sa.Column("id",   sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column("nome", sa.String(100), nullable=False, unique=True),
    )

    op.create_table("documentos_contabeis",
        sa.Column("id",                sa.Integer(),      primary_key=True, autoincrement=True),
        sa.Column("numero",            sa.String(100),    nullable=False),
        sa.Column("tipo_documento_id", sa.Integer(),      sa.ForeignKey("tipos_doc.id"), nullable=False),
        sa.Column("contrato_id",       sa.Integer(),      sa.ForeignKey("contratos.id"), nullable=False),
        sa.Column("valor",             sa.Numeric(14, 2), nullable=False),
        sa.Column("criado_em",         sa.DateTime(),     server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )

    op.create_table("tipos_impressora",
        sa.Column("id",   sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column("tipo", sa.String(100), nullable=False, unique=True),
    )

    op.create_table("locais_impressora",
        sa.Column("id",        sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column("setor",     sa.String(100), nullable=False),
        sa.Column("descricao", sa.String(300), nullable=False),
    )

    op.create_table("modelos_impressora",
        sa.Column("id",         sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column("fabricante", sa.String(100), nullable=False),
        sa.Column("modelo",     sa.String(200), nullable=False),
        sa.Column("descricao",  sa.String(500), nullable=True),
    )

    op.create_table("impressoras",
        sa.Column("num_serie", sa.String(100), primary_key=True),
        sa.Column("tipo_id",   sa.Integer(),   sa.ForeignKey("tipos_impressora.id"),   nullable=False),
        sa.Column("local_id",  sa.Integer(),   sa.ForeignKey("locais_impressora.id"),  nullable=False),
        sa.Column("modelo_id", sa.Integer(),   sa.ForeignKey("modelos_impressora.id"), nullable=True),
        sa.Column("ip",        sa.String(45),  nullable=True),
        sa.Column("ativa",     sa.Boolean(),   nullable=False, server_default="1"),
        sa.Column("criado_em", sa.DateTime(),  server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )

    op.create_table("tipos_impressao",
        sa.Column("id",        sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column("descricao", sa.String(200), nullable=False, unique=True),
    )

    # Franquia por contrato: total de páginas + custo fixo mensal
    op.create_table("franquias_contrato",
        sa.Column("id",                   sa.Integer(),      primary_key=True, autoincrement=True),
        sa.Column("contrato_id",          sa.Integer(),      sa.ForeignKey("contratos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo_impressao_id",    sa.Integer(),      sa.ForeignKey("tipos_impressao.id"), nullable=False),
        sa.Column("paginas_franquia",     sa.Integer(),      nullable=False),
        sa.Column("valor_mensal_franquia",sa.Numeric(14, 2), nullable=False, server_default="0"),
    )

    # Tabela de preços com histórico — registros históricos NUNCA são alterados
    op.create_table("tabelas_preco",
        sa.Column("id",                    sa.Integer(),       primary_key=True, autoincrement=True),
        sa.Column("contrato_id",           sa.Integer(),       sa.ForeignKey("contratos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo_impressao_id",     sa.Integer(),       sa.ForeignKey("tipos_impressao.id"), nullable=False),
        sa.Column("valor_dentro_franquia", sa.Numeric(14, 6),  nullable=False),
        sa.Column("valor_fora_franquia",   sa.Numeric(14, 6),  nullable=False),
        sa.Column("vigente_de",            sa.Date(),          nullable=False),
        sa.Column("vigente_ate",           sa.Date(),          nullable=True),
        sa.Column("criado_em",             sa.DateTime(),      server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )

    # Leituras de contadores — vinculadas ao contrato para contexto de franquia
    op.create_table("leituras",
        sa.Column("id",                   sa.Integer(),  primary_key=True, autoincrement=True),
        sa.Column("contrato_id",          sa.Integer(),  sa.ForeignKey("contratos.id"), nullable=False),
        sa.Column("impressora_num_serie", sa.String(100),sa.ForeignKey("impressoras.num_serie"), nullable=False),
        sa.Column("tipo_impressao_id",    sa.Integer(),  sa.ForeignKey("tipos_impressao.id"), nullable=False),
        sa.Column("contador",             sa.Integer(),  nullable=False),
        sa.Column("data",                 sa.Date(),     nullable=False),
        sa.Column("mes_referencia",       sa.Integer(),  nullable=False),
        sa.Column("ano_referencia",       sa.Integer(),  nullable=False),
        sa.Column("manual",               sa.Boolean(),  nullable=False, server_default="0"),
        sa.Column("observacao",           sa.Text(),     nullable=True),
        sa.Column("criado_em",            sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_index("ix_leituras_contrato", "leituras", ["contrato_id"])
    op.create_index("ix_leituras_impressora", "leituras", ["impressora_num_serie"])

    # Seeds de tipos de documento
    op.execute("INSERT INTO tipos_doc (nome) VALUES ('NE'), ('OB'), ('RP'), ('NS')")


def downgrade() -> None:
    op.drop_table("leituras")
    op.drop_table("tabelas_preco")
    op.drop_table("franquias_contrato")
    op.drop_table("tipos_impressao")
    op.drop_table("impressoras")
    op.drop_table("modelos_impressora")
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
