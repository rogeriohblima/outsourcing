#!/bin/sh
# entrypoint.sh — Executa migrations do Alembic e inicia o servidor Uvicorn.
#
# Fluxo:
#   1. Aguarda o banco de dados ficar pronto (retry com backoff)
#   2. Aplica todas as migrations pendentes (alembic upgrade head)
#   3. Inicia o servidor Uvicorn
#
# Em caso de falha nas migrations, o container é encerrado com erro
# para que o orquestrador (Docker Compose / Kubernetes) possa reiniciar.

set -e

echo "[entrypoint] Aguardando banco de dados…"

# Aguarda até 60s para o banco aceitar conexões
MAX_TRIES=30
WAIT=2
i=0
until python -c "
import sys, os
try:
    import psycopg2
    psycopg2.connect(os.environ.get('SYNC_DATABASE_URL',''))
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    i=$((i + 1))
    if [ $i -ge $MAX_TRIES ]; then
        echo "[entrypoint] ERRO: banco de dados não respondeu após ${MAX_TRIES} tentativas." >&2
        exit 1
    fi
    echo "[entrypoint] Tentativa $i/$MAX_TRIES — aguardando ${WAIT}s…"
    sleep $WAIT
done

echo "[entrypoint] Banco disponível. Executando migrations…"
alembic upgrade head

echo "[entrypoint] Migrations concluídas. Iniciando servidor…"
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --log-level info
