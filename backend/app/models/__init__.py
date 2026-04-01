"""
app/models/__init__.py — Importa todos os modelos para que o Alembic
os detecte automaticamente via Base.metadata durante a geração de migrações.

Este arquivo deve ser importado em alembic/env.py antes de qualquer
chamada ao autogenerate.
"""

from app.models.models import (  # noqa: F401
    Membro,
    Comissao,
    Empresa,
    Contrato,
    Fatura,
    TipoDoc,
    DocumentoContabil,
    TipoImpressora,
    LocalImpressora,
    Impressora,
    TipoImpressao,
    Leitura,
    comissao_fiscais,
)
