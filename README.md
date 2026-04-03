# 🖨️ Sistema de Gerenciamento de Contratos de Impressoras

Sistema desenvolvido para **Organizações Militares da Aeronáutica** para gerenciar contratos de impressoras, incluindo leitura automática de contadores via SNMP, relatórios mensais e totais, e controle de faturas e documentos contábeis.

## 📋 Funcionalidades

- **Autenticação via Active Directory** (JWT + LDAP)
- **CRUD completo** para todas as entidades do sistema
- **Leitura automática de contadores** via SNMP (com fallback manual)
- **Relatórios mensais e totais**: consumo, valores, franquias, percentuais de orçamento e tempo
- **Gerenciamento de comissões fiscais** com membros e documentos
- **Controle de faturas e documentos contábeis** por contrato
- **Suporte a PostgreSQL** (produção) e **SQLite** (desenvolvimento/testes)

## 🏗️ Arquitetura

```
sistema-contrato-impressora/
├── backend/          # API REST com FastAPI
│   ├── app/
│   │   ├── auth/     # Autenticação JWT + Active Directory
│   │   ├── models/   # Modelos SQLAlchemy
│   │   ├── schemas/  # Schemas Pydantic v2
│   │   ├── routers/  # Endpoints da API
│   │   └── services/ # Lógica de negócio e SNMP
│   ├── tests/        # Testes unitários
│   └── alembic/      # Migrações de banco de dados
└── frontend/         # SPA com React + TypeScript
    └── src/
        ├── api/      # Client HTTP (Axios)
        ├── auth/     # Contexto de autenticação
        ├── components/
        ├── pages/    # Páginas por entidade
        └── types/    # Tipos TypeScript
```

## 🛠️ Tecnologias

### Backend
| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.11+ | Linguagem base |
| FastAPI | 0.115+ | Framework web |
| SQLAlchemy | 2.0+ | ORM (async) |
| Pydantic | 2.0+ | Validação de dados |
| python-jose | 3.3+ | Tokens JWT |
| ldap3 | 2.9+ | Autenticação Active Directory |
| pysnmp | 6.1+ | Leitura de contadores via SNMP |
| Alembic | 1.13+ | Migrações de banco |
| asyncpg | 0.29+ | Driver PostgreSQL async |
| aiosqlite | 0.20+ | Driver SQLite async |
| pytest | 8.0+ | Testes unitários |
| httpx | 0.27+ | Cliente HTTP para testes |

### Frontend
| Tecnologia | Versão | Uso |
|---|---|---|
| React | 18+ | Framework UI |
| TypeScript | 5+ | Tipagem estática |
| Vite | 5+ | Build tool |
| React Router | 6+ | Roteamento |
| TanStack Query | 5+ | Gerenciamento de estado/cache |
| Axios | 1.7+ | Cliente HTTP |
| Tailwind CSS | 3+ | Estilização |
| React Hook Form | 7+ | Formulários |
| Zod | 3+ | Validação de schemas |
| Recharts | 2+ | Gráficos e relatórios |
| shadcn/ui | latest | Componentes UI |

## ⚙️ Configuração

### Pré-requisitos
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (produção) ou SQLite (desenvolvimento)
- Acesso ao servidor Active Directory (192.168.0.1)
- Rede com acesso SNMP às impressoras

### Backend

1. **Clone o repositório e acesse o backend:**
```bash
cd backend
```

2. **Crie e ative o ambiente virtual:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. **Execute as migrações:**
```bash
# PostgreSQL (produção)
alembic upgrade head

# SQLite (desenvolvimento) — cria automaticamente
```

6. **Inicie o servidor:**
```bash
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000`.  
Documentação interativa: `http://localhost:8000/docs`

### Frontend

1. **Acesse o diretório do frontend:**
```bash
cd frontend
```

2. **Instale as dependências:**
```bash
npm install
```

3. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
# Configure VITE_API_URL=http://localhost:8000
```

4. **Inicie o servidor de desenvolvimento:**
```bash
npm run dev
```

O frontend estará disponível em `http://localhost:5173`.

## 🔑 Configuração do Active Directory

No arquivo `.env`, configure:

```env
AD_SERVER=<IP_AD>
AD_DOMAIN=<sua.organizacao.com.br>
AD_BASE_DN=DC=sua,DC=organizacao,DC=com,DC=br
AD_USE_SSL=false
```

## 🗄️ Banco de Dados

### PostgreSQL (produção)
```env
DATABASE_URL=postgresql+asyncpg://usuario:senha@localhost:5432/contrato_impressoras
```

### SQLite (desenvolvimento)
```env
DATABASE_URL=sqlite+aiosqlite:///./contrato_impressoras.db
```

## 📡 SNMP

O sistema tenta ler os contadores de impressão via SNMP (v2c) nos seguintes OIDs padrão:
- `1.3.6.1.2.1.43.10.2.1.4.1.1` — Total de páginas (prtMarkerLifeCount)
- OIDs específicos por fabricante (HP, Xerox, Ricoh, Canon, Lexmark)

Se a leitura automática falhar, o sistema permite o lançamento manual do contador.

**Configuração SNMP:**
```env
SNMP_COMMUNITY=public
SNMP_PORT=161
SNMP_TIMEOUT=5
SNMP_RETRIES=2
```

## 🧪 Testes

```bash
cd backend

# Todos os testes (usa SQLite automaticamente)
pytest

# Com cobertura de código
pytest --cov=app --cov-report=html

# Testes específicos
pytest tests/test_impressoras.py -v
pytest tests/test_leituras.py -v
pytest tests/test_relatorios.py -v
```

## 📊 Relatórios Disponíveis

- **Consumo Mensal**: páginas impressas por impressora/tipo de impressão
- **Consumo por Contrato**: total de páginas e valores por período
- **Comparativo Franquia vs. Excedente**: análise de uso dentro e fora da franquia
- **Percentual de Orçamento Consumido**: valor faturado vs. valor contratado
- **Percentual de Tempo Decorrido**: dias corridos vs. prazo total do contrato
- **Evolução Mensal**: gráfico de consumo ao longo do tempo
- **Impressoras Mais Utilizadas**: ranking por volume de impressão
- **Faturas por Contrato**: resumo financeiro por período

## 🔒 Segurança

- Autenticação exclusivamente via Active Directory — sem cadastro local de senhas
- Tokens JWT com expiração configurável
- HTTPS recomendado em produção
- Variáveis sensíveis via `.env` (nunca comitar)

## 📝 Variáveis de Ambiente

Veja `.env.example` para a lista completa de variáveis de ambiente necessárias.

## 🤝 Contribuição

1. Crie uma branch: `git checkout -b feature/minha-funcionalidade`
2. Commit: `git commit -m 'feat: descrição da funcionalidade'`
3. Push: `git push origin feature/minha-funcionalidade`
4. Abra um Pull Request

## 📄 Licença

Uso interno.

---
