#!/bin/bash
# check_db.sh — Verifica estrutura das tabelas no banco SQLite
# Execute: bash check_db.sh

DB=$(find . -name "*.db" 2>/dev/null | head -1)
if [ -z "$DB" ]; then
    echo "Banco SQLite nao encontrado. Verifique o .env (DATABASE_URL)"
    exit 1
fi

echo "Banco: $DB"
echo ""
echo "=== Colunas da tabela faturas ==="
sqlite3 "$DB" "PRAGMA table_info(faturas);"
echo ""
echo "=== Colunas da tabela leituras ==="
sqlite3 "$DB" "PRAGMA table_info(leituras);" | grep -E "nome|contrato"
