# Guia de Contribuição — SCI

## Estrutura do Projeto

```
sistema-contrato-impressora/
│
├── backend/                    # API REST (FastAPI + SQLAlchemy 2.0)
│   ├── app/
│   │   ├── auth/               # Autenticação JWT + Active Directory
│   │   │   ├── dependencies.py # Dependency injection do usuário autenticado
│   │   │   ├── router.py       # Endpoints /auth/login e /auth/me
│   │   │   ├── schemas.py      # Schemas Pydantic de autenticação
│   │   │   └── service.py      # Lógica LDAP/AD + geração JWT
│   │   ├── models/
│   │   │   └── models.py       # Todos os modelos ORM SQLAlchemy 2.0
│   │   ├── routers/            # Um arquivo por entidade (CRUD)
│   │   ├── schemas/
│   │   │   └── schemas.py      # Todos os schemas Pydantic (entrada/saída)
│   │   ├── services/
│   │   │   ├── snmp_service.py      # Leitura de contadores via SNMP
│   │   │   └── relatorio_service.py # Cálculos financeiros de relatórios
│   │   ├── config.py           # Configurações via pydantic-settings
│   │   ├── database.py         # Engine assíncrona + session factory
│   │   └── main.py             # Aplicação FastAPI + registro de routers
│   ├── alembic/                # Migrações de banco de dados
│   │   └── versions/           # Scripts de migração
│   └── tests/                  # Testes unitários (pytest + pytest-asyncio)
│
└── frontend/                   # SPA React + TypeScript + Vite
    └── src/
        ├── api/
        │   ├── client.ts       # Instância Axios + interceptors JWT
        │   └── endpoints.ts    # Funções de chamada por entidade
        ├── auth/
        │   ├── AuthContext.tsx  # Contexto global de autenticação
        │   └── ProtectedRoute.tsx # HOC de proteção de rotas
        ├── components/
        │   ├── common/         # Componentes reutilizáveis (Modal, Alert, etc.)
        │   └── layout/         # Layout principal com sidebar
        ├── hooks/
        │   └── index.ts        # Custom hooks (TanStack Query)
        ├── pages/              # Uma pasta por página/entidade
        ├── types/
        │   └── index.ts        # Todos os tipos TypeScript
        └── utils/
            └── index.ts        # Utilitários (formatadores, validadores)
```

## Convenções de Código

### Backend (Python)

**Nomenclatura:**
- Funções e variáveis: `snake_case`
- Classes: `PascalCase`
- Constantes: `UPPER_SNAKE_CASE`
- Arquivos: `snake_case.py`

**Routers:**
- Cada router recebe seu próprio arquivo em `app/routers/`
- Prefixo de URL no `main.py`, não no router
- Dependency injection via `Depends(get_db)` e `Depends(get_current_user)`
- Schemas de resposta sempre declarados em `response_model=`

**Banco de Dados:**
- Sempre usar `AsyncSession` com `await`
- Carregar relacionamentos com `selectinload()` para evitar N+1
- Usar `db.flush()` dentro de mutations (commit pelo middleware do `get_db`)
- Migrações via Alembic — nunca usar `create_all` em produção

**Testes:**
- Usar `pytest-asyncio` com `asyncio_mode = auto`
- Banco SQLite em memória via fixture `db` do `conftest.py`
- Mockar serviços externos (SNMP, AD) com `unittest.mock.patch`
- Documentar cada teste explicando o cenário e a expectativa

### Frontend (TypeScript)

**Nomenclatura:**
- Componentes: `PascalCase`
- Funções e variáveis: `camelCase`
- Arquivos de componente: `PascalCase.tsx`
- Tipos/interfaces: sufixo `Out` (resposta API) ou `Form` (formulários)

**Estado e Cache:**
- Estado remoto: TanStack Query (nunca `useState` para dados da API)
- Estado local de UI: `useState` (modais, erros de formulário, etc.)
- Chaves de query centralizadas no `hooks/index.ts` (`QUERY_KEYS`)

**Formulários:**
- React Hook Form + Zod para validação
- Schemas Zod espelham os schemas Pydantic do backend
- Sempre invalidar as queries relevantes após mutations

**Estilização:**
- Tailwind CSS com classes utilitárias
- Classes customizadas em `index.css` via `@layer components`
- Paleta da FAB definida em `tailwind.config.js`

## Adicionando uma Nova Entidade

### Backend

1. **Model** (`app/models/models.py`): adicione a classe SQLAlchemy
2. **Schema** (`app/schemas/schemas.py`): crie `Base`, `Create`, `Update`, `Out`
3. **Router** (`app/routers/nova_entidade.py`): implemente os 5 endpoints CRUD
4. **Registrar** no `app/main.py`: `app.include_router(nova_router, prefix=PREFIX)`
5. **Migration**: `alembic revision --autogenerate -m "add nova_entidade"`
6. **Testes**: crie `tests/test_nova_entidade.py` seguindo os exemplos existentes

### Frontend

1. **Tipos** (`src/types/index.ts`): adicione `NovaEntidadeOut` e `NovaEntidadeForm`
2. **Endpoints** (`src/api/endpoints.ts`): adicione `novaEntidadeApi` com list/get/create/update/remove
3. **Hook** (`src/hooks/index.ts`): adicione `useNovaEntidade()` se necessário
4. **Página** (`src/pages/nova-entidade/NovaEntidadePage.tsx`): crie o CRUD completo
5. **Rota** (`src/App.tsx`): adicione `<Route path="nova-entidade" element={<NovaEntidadePage />} />`
6. **Menu** (`src/components/layout/Layout.tsx`): adicione item no `menuGroups`

## Fluxo de Desenvolvimento

```bash
# 1. Fork e clone
git clone https://github.com/seu-fork/sistema-contrato-impressora.git
cd sistema-contrato-impressora

# 2. Instala dependências
make install

# 3. Cria branch de feature
git checkout -b feature/minha-funcionalidade

# 4. Desenvolve (backend com hot-reload, banco SQLite automático)
make backend   # em um terminal
make frontend  # em outro terminal

# 5. Executa testes
make test

# 6. Verifica lint
make lint

# 7. Commit e Push
git add .
git commit -m "feat: descrição clara da funcionalidade"
git push origin feature/minha-funcionalidade

# 8. Abre Pull Request
```

## Mensagens de Commit (Conventional Commits)

```
feat:     nova funcionalidade
fix:      correção de bug
docs:     documentação
style:    formatação (sem mudança de lógica)
refactor: refatoração sem nova funcionalidade
test:     adiciona ou corrige testes
chore:    tarefas de manutenção (deps, CI, etc.)
```

## Variáveis de Ambiente Obrigatórias

| Variável | Descrição | Exemplo |
|---|---|---|
| `DATABASE_URL` | URL assíncrona do banco | `postgresql+asyncpg://...` |
| `SYNC_DATABASE_URL` | URL síncrona (Alembic) | `postgresql+psycopg2://...` |
| `SECRET_KEY` | Chave JWT (64 hex chars) | `openssl rand -hex 32` |
| `AD_SERVER` | IP do Active Directory | `10.10.10.10` |
| `AD_DOMAIN` | Domínio do AD | `organizacao.mil.br` |
| `AD_BASE_DN` | Base DN do AD | `DC=organizacao,DC=mil,DC=br` |

## Segurança — Itens Obrigatórios em Produção

- [ ] `SECRET_KEY` gerada com `openssl rand -hex 32` (não usar a padrão)
- [ ] `APP_ENV=production` (desativa docs e credenciais de dev)
- [ ] `DEBUG=false`
- [ ] Banco PostgreSQL com usuário dedicado (sem superuser)
- [ ] HTTPS configurado no proxy reverso (Nginx)
- [ ] Arquivo `.env` fora do repositório
- [ ] Conta de serviço do AD com permissão somente de leitura

## Dúvidas

Em caso de dúvidas técnicas sobre o sistema, contate o SETIC da Organização Militar.
