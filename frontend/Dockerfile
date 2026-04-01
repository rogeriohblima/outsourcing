# ── Frontend Dockerfile ─────────────────────────────────────────────────────────
# Build multi-stage:
#   1. Node.js: faz o build da SPA React com Vite
#   2. Nginx:   serve os arquivos estáticos e faz proxy para a API

# Etapa 1: build React
FROM node:20-alpine AS builder

ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

WORKDIR /app

COPY package*.json ./
RUN npm ci --silent

COPY . .
RUN npm run build


# Etapa 2: servidor Nginx
FROM nginx:1.27-alpine

LABEL maintainer="SETIC — Organização Militar da Aeronáutica"
LABEL description="Frontend do Sistema de Contratos de Impressoras (SCI)"

# Copia os arquivos buildados
COPY --from=builder /app/dist /usr/share/nginx/html

# Configuração customizada do Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
