#!/bin/bash
# diagnostico.sh — Execute na raiz do projeto para diagnosticar o erro 502
# Uso: bash diagnostico.sh

echo "========================================"
echo " Diagnostico SCI — Erro 502"
echo "========================================"
echo ""

echo "1. Status dos containers:"
docker compose ps
echo ""

echo "2. Logs do BACKEND (ultimas 50 linhas):"
docker compose logs --tail=50 backend
echo ""

echo "3. Logs do FRONTEND/Nginx (ultimas 20 linhas):"
docker compose logs --tail=20 frontend
echo ""

echo "4. Teste de conectividade interno (frontend -> backend):"
docker compose exec frontend wget -q -O- http://backend:8000/health 2>&1 || echo "FALHOU — frontend nao alcanca o backend"
echo ""

echo "5. Teste direto no backend:"
docker compose exec backend curl -s http://localhost:8000/health 2>&1 || \
  wget -q -O- http://localhost:8000/health 2>&1 || \
  echo "FALHOU — backend nao responde internamente"
echo ""

echo "========================================"
echo " Cole a saida acima para diagnostico"
echo "========================================"
