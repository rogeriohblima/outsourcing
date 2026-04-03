#!/bin/sh
# entrypoint.sh — Aguarda PostgreSQL, aplica migrations e inicia o servidor.
set -e

echo "[entrypoint] Iniciando SCI Backend..."
echo "[entrypoint] APP_ENV=${APP_ENV}"

# Extrai host e porta da DATABASE_URL para usar no pg_isready
# Exemplo: postgresql+asyncpg://sci_user:senha@postgres:5432/contrato_impressoras
#          => host=postgres porta=5432
DB_HOST=$(echo "$DATABASE_URL" | sed 's|.*@||' | sed 's|:.*||' | sed 's|/.*||')
DB_PORT=$(echo "$DATABASE_URL" | sed 's|.*:||' | sed 's|/.*||')
DB_USER=$(echo "$DATABASE_URL" | sed 's|.*://||' | sed 's|:.*||')

# Se nao for PostgreSQL (ex: SQLite), pula a espera
if echo "$DATABASE_URL" | grep -q "postgresql"; then
    echo "[entrypoint] Aguardando PostgreSQL em ${DB_HOST}:${DB_PORT}..."
    MAX_TRIES=30
    i=0
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q; do
        i=$((i + 1))
        if [ $i -ge $MAX_TRIES ]; then
            echo "[entrypoint] ERRO: PostgreSQL nao respondeu apos ${MAX_TRIES} tentativas."
            exit 1
        fi
        echo "[entrypoint] Tentativa $i/$MAX_TRIES — aguardando 2s..."
        sleep 2
    done
    echo "[entrypoint] PostgreSQL disponivel!"
else
    echo "[entrypoint] SQLite detectado — sem espera necessaria."
fi

# Aplica migrations
echo "[entrypoint] Aplicando migrations..."
alembic upgrade head
echo "[entrypoint] Migrations aplicadas!"

# Inicia o servidor
echo "[entrypoint] Iniciando Uvicorn na porta 8000..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --log-level info