"""
fix_db.py — Verifica e corrige a estrutura do banco SQLite.

Adiciona colunas faltantes sem apagar os dados existentes.
Execute: python fix_db.py (na pasta backend/)
"""

import sqlite3
import os
import sys
from pathlib import Path

# Localiza o banco de dados
db_path = None
for candidate in [
    "./contrato_impressoras.db",
    "./contrato_impressoras_dev.db",
    "./data/contrato_impressoras.db",
]:
    if os.path.exists(candidate):
        db_path = candidate
        break

if not db_path:
    print("ERRO: Banco SQLite nao encontrado.")
    print("Verifique o arquivo .env — DATABASE_URL deve apontar para o .db correto.")
    sys.exit(1)

print(f"Banco encontrado: {db_path}")
print()

conn = sqlite3.connect(db_path)
cur  = conn.cursor()

# ── Colunas a garantir por tabela ─────────────────────────────────────────────
# Formato: (tabela, coluna, tipo_sql, valor_default)
COLUNAS_NECESSARIAS = [
    # Fatura — novos campos
    ("faturas", "mes_referencia", "INTEGER NOT NULL DEFAULT 1"),
    ("faturas", "ano_referencia", "INTEGER NOT NULL DEFAULT 2025"),
    ("faturas", "valor",          "NUMERIC(14,2) NOT NULL DEFAULT 0"),

    # Impressoras — campo modelo_id (caso não exista)
    ("impressoras", "modelo_id", "INTEGER REFERENCES modelos_impressora(id)"),

    # Contratos — campo valor_estimado (caso não exista)
    ("contratos", "valor_estimado", "NUMERIC(14,2) NOT NULL DEFAULT 0"),

    # Leituras — campo contrato_id (caso não exista)
    ("leituras", "contrato_id", "INTEGER REFERENCES contratos(id)"),
]

def colunas_existentes(tabela):
    cur.execute(f"PRAGMA table_info({tabela})")
    return {row[1] for row in cur.fetchall()}

correcoes = 0
erros = 0

for tabela, coluna, tipo_sql in COLUNAS_NECESSARIAS:
    try:
        existentes = colunas_existentes(tabela)
        if coluna not in existentes:
            cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo_sql}")
            conn.commit()
            print(f"  [ADICIONADO] {tabela}.{coluna}")
            correcoes += 1
        else:
            print(f"  [OK]         {tabela}.{coluna}")
    except Exception as e:
        print(f"  [ERRO]       {tabela}.{coluna} — {e}")
        erros += 1

# ── Verifica tabelas novas ────────────────────────────────────────────────────
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tabelas = {row[0] for row in cur.fetchall()}

tabelas_necessarias = [
    "modelos_impressora",
    "franquias_contrato",
    "tabelas_preco",
]

print()
print("=== Tabelas necessárias ===")
for t in tabelas_necessarias:
    if t in tabelas:
        print(f"  [OK]      {t}")
    else:
        print(f"  [FALTA]   {t}  ← rode: bash reset_db.sh && docker compose restart backend")

conn.close()

print()
if correcoes > 0:
    print(f"Correções aplicadas: {correcoes} coluna(s) adicionada(s).")
    print("Reinicie o backend para que as mudanças tenham efeito.")
elif erros == 0:
    print("Banco já está na estrutura correta!")

if erros > 0:
    print(f"Erros encontrados: {erros}. Verifique as mensagens acima.")
