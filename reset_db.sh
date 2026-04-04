#!/bin/bash
# reset_db.sh — Apaga o banco SQLite e recria do zero.
# Execute na raiz do projeto.

set -e

DB_PATH="backend/contrato_impressoras.db"

echo "=== Reset do Banco de Dados SQLite ==="
echo ""

if [ -f "$DB_PATH" ]; then
    echo "  Removendo banco antigo: $DB_PATH"
    rm -f "$DB_PATH"
    echo "  [OK] Banco removido."
else
    echo "  [--] Banco nao encontrado em $DB_PATH"
fi

# Remove também o banco na pasta data/ se existir
if [ -f "backend/data/contrato_impressoras.db" ]; then
    echo "  Removendo banco em backend/data/..."
    rm -f "backend/data/contrato_impressoras.db"
    echo "  [OK] Banco em data/ removido."
fi

echo ""
echo "  Reinicie o backend para recriar as tabelas automaticamente:"
echo "    docker compose restart backend"
echo "    # ou"
echo "    cd backend && uvicorn app.main:app --reload"
echo ""
echo "  Em seguida execute o seed:"
echo "    docker compose exec backend python seed.py"
echo "    # ou"
echo "    cd backend && python seed.py"
