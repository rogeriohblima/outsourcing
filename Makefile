# Makefile — Atalhos de desenvolvimento para o SCI
#
# Uso:
#   make help          → Exibe esta ajuda
#   make dev           → Inicia backend e frontend em modo dev
#   make backend       → Inicia apenas o backend (SQLite)
#   make frontend      → Inicia apenas o frontend
#   make test          → Executa todos os testes unitários
#   make test-cov      → Testes com relatório de cobertura HTML
#   make migrate       → Aplica migrations (PostgreSQL)
#   make migrate-new   → Cria nova migration automática
#   make docker-up     → Sobe o stack completo com Docker Compose
#   make docker-down   → Para o stack Docker
#   make docker-logs   → Exibe logs dos containers
#   make lint          → Lint do frontend (ESLint)
#   make clean         → Remove arquivos temporários

.PHONY: help dev backend frontend test test-cov migrate migrate-new \
        docker-up docker-down docker-logs lint clean install

PYTHON     := python3
PIP        := pip3
VENV       := backend/venv
UVICORN    := $(VENV)/bin/uvicorn
PYTEST     := $(VENV)/bin/pytest
ALEMBIC    := $(VENV)/bin/alembic

# ── Ajuda ─────────────────────────────────────────────────────────────────────

help:  ## Exibe esta mensagem de ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Instalação ────────────────────────────────────────────────────────────────

install:  ## Instala todas as dependências (backend e frontend)
	@echo "==> Instalando dependências do backend…"
	cd backend && $(PYTHON) -m venv venv && $(PIP) install -r requirements.txt
	@echo "==> Instalando dependências do frontend…"
	cd frontend && npm install
	@echo "==> Copiando arquivos .env de exemplo…"
	test -f backend/.env || cp backend/.env.example backend/.env
	test -f frontend/.env || cp frontend/.env.example frontend/.env
	@echo "✅ Instalação concluída! Edite backend/.env com suas configurações."

# ── Desenvolvimento ───────────────────────────────────────────────────────────

backend:  ## Inicia o backend FastAPI (SQLite automático)
	cd backend && $(UVICORN) app.main:app --reload --port 8000

frontend:  ## Inicia o frontend React (modo dev)
	cd frontend && npm run dev

# Inicia backend e frontend em paralelo (requer 'make' com suporte a &)
dev:  ## Inicia backend e frontend simultaneamente
	@echo "==> Iniciando backend em background…"
	cd backend && $(UVICORN) app.main:app --reload --port 8000 &
	@echo "==> Iniciando frontend…"
	cd frontend && npm run dev

# ── Testes ────────────────────────────────────────────────────────────────────

test:  ## Executa todos os testes unitários
	cd backend && $(PYTEST) -v

test-cov:  ## Testes com relatório de cobertura HTML
	cd backend && $(PYTEST) --cov=app --cov-report=html --cov-report=term-missing
	@echo "==> Relatório em: backend/htmlcov/index.html"

test-auth:  ## Executa apenas os testes de autenticação
	cd backend && $(PYTEST) tests/test_auth.py -v

test-leituras:  ## Executa apenas os testes de leituras
	cd backend && $(PYTEST) tests/test_leituras.py -v

test-relatorios:  ## Executa apenas os testes de relatórios
	cd backend && $(PYTEST) tests/test_relatorios.py -v

# ── Banco de Dados / Migrations ───────────────────────────────────────────────

migrate:  ## Aplica todas as migrations pendentes
	cd backend && $(ALEMBIC) upgrade head

migrate-new:  ## Cria nova migration automática (use msg="descricao")
	cd backend && $(ALEMBIC) revision --autogenerate -m "$(msg)"

migrate-history:  ## Exibe histórico de migrations
	cd backend && $(ALEMBIC) history --verbose

migrate-down:  ## Reverte a última migration
	cd backend && $(ALEMBIC) downgrade -1

# ── Docker ────────────────────────────────────────────────────────────────────

docker-up:  ## Sobe o stack completo (PostgreSQL + Backend + Frontend)
	docker compose up --build -d
	@echo "✅ Stack iniciado!"
	@echo "   Frontend: http://localhost"
	@echo "   Backend:  http://localhost:8000/docs"

docker-down:  ## Para e remove os containers
	docker compose down

docker-logs:  ## Exibe logs de todos os containers em tempo real
	docker compose logs -f

docker-backend-logs:  ## Exibe logs apenas do backend
	docker compose logs -f backend

docker-restart-backend:  ## Reinicia o container do backend
	docker compose restart backend

docker-shell-backend:  ## Abre shell no container do backend
	docker compose exec backend sh

docker-psql:  ## Abre o psql no container do PostgreSQL
	docker compose exec postgres psql -U $${POSTGRES_USER:-sci_user} -d $${POSTGRES_DB:-contrato_impressoras}

# ── Qualidade de Código ───────────────────────────────────────────────────────

lint:  ## Executa ESLint no frontend
	cd frontend && npm run lint

lint-fix:  ## Corrige erros de lint automaticamente
	cd frontend && npm run lint -- --fix

# ── Limpeza ───────────────────────────────────────────────────────────────────

clean:  ## Remove arquivos temporários e caches
	find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find backend -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/.pytest_cache backend/htmlcov backend/.coverage 2>/dev/null || true
	rm -rf frontend/dist frontend/.vite 2>/dev/null || true
	@echo "✅ Limpeza concluída."

# ── Utilitários ───────────────────────────────────────────────────────────────

generate-secret:  ## Gera uma SECRET_KEY segura para o .env
	@python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

check-snmp:  ## Testa SNMP de uma impressora (use ip=192.168.x.x)
	@$(PYTHON) -c "
import asyncio, sys
sys.path.insert(0, 'backend')
from app.services.snmp_service import testar_conectividade_snmp
r = asyncio.run(testar_conectividade_snmp('$(ip)'))
print(r)
"
