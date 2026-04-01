# ── Backend Dockerfile ─────────────────────────────────────────────────────────
# Build multi-stage: instala dependências em uma etapa separada para
# reduzir o tamanho da imagem final.

# Etapa 1: build de dependências
FROM python:3.11-slim AS builder

WORKDIR /build

# Instala dependências de compilação (para pysnmp, asyncpg, ldap3)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libldap2-dev libsasl2-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Etapa 2: imagem de produção
FROM python:3.11-slim

LABEL maintainer="SETIC — Organização Militar da Aeronáutica"
LABEL description="API do Sistema de Contratos de Impressoras (SCI)"

# Runtime deps para ldap3 e asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libldap-2.5-0 libsasl2-2 \
    && rm -rf /var/lib/apt/lists/*

# Copia pacotes instalados do builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copia o código da aplicação
COPY . .

# Cria diretório de uploads
RUN mkdir -p /app/uploads

# Variáveis de ambiente padrão (podem ser sobrescritas no docker-compose)
ENV APP_ENV=production \
    DEBUG=false \
    UPLOAD_DIR=/app/uploads

# Script de entrypoint: executa migrations + inicia o servidor
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
