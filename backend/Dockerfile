# ── Backend Dockerfile ───────────────────────────────────────────────────────

# Etapa 1: compilacao das dependencias
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libssl-dev \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Etapa 2: imagem de runtime
FROM python:3.11-slim

LABEL maintainer="SETIC"
LABEL description="API do Sistema de Contratos de Impressoras (SCI)"

# libpq5         — runtime do psycopg2-binary
# postgresql-client — fornece o pg_isready usado no entrypoint
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

WORKDIR /app

COPY . .

RUN chmod +x /app/entrypoint.sh \
    && mkdir -p /app/uploads

ENV APP_ENV=production \
    DEBUG=false \
    UPLOAD_DIR=/app/uploads \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]