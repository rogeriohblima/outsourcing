# Guia Docker — SCI Sistema de Contratos de Impressoras

## Pre-requisitos

Instale o **Docker Desktop** no computador de destino:
- Windows: https://www.docker.com/products/docker-desktop/
- Aceite os termos e reinicie o computador se solicitado
- Verifique a instalacao: `docker --version`

---

## Estrutura dos arquivos Docker

```
sistema-contrato-impressora/
├── docker-compose.yml        ← orquestra os 3 containers
├── .env                      ← variaveis de ambiente (voce cria)
├── backend/
│   ├── Dockerfile            ← build da API Python
│   └── entrypoint.sh         ← roda migrations + inicia uvicorn
└── frontend/
    ├── Dockerfile            ← build do React + Nginx
    └── nginx.conf            ← proxy /api/* para o backend
```

---

## Passo a passo

### 1. Preparar o .env

Na raiz do projeto, crie o arquivo `.env` com o conteudo abaixo.
**Nunca comite este arquivo no Git.**

```env
# PostgreSQL
POSTGRES_DB=contrato_impressoras
POSTGRES_USER=sci_user
POSTGRES_PASSWORD=SenhaForteAqui123

# Aplicacao
APP_ENV=development
DEBUG=true
SECRET_KEY=troque-por-chave-hex-de-64-chars

# AD (ignorado em development)
AD_SERVER=10.10.10.10
AD_DOMAIN=organizacao.mil.br
AD_BASE_DN=DC=organizacao,DC=mil,DC=br
```

Para gerar a SECRET_KEY, abra o PowerShell e execute:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### 2. Construir e iniciar os containers

Abra o PowerShell ou Terminal na raiz do projeto e execute:

```powershell
# Constroi as imagens e sobe os containers em segundo plano
docker compose up --build -d
```

Na primeira execucao isso pode demorar 5-10 minutos (download das
imagens base e instalacao dos pacotes Python e Node.js).

---

### 3. Verificar se esta rodando

```powershell
# Mostra o status dos containers
docker compose ps

# Resultado esperado:
# NAME            STATUS          PORTS
# sci_postgres    Up (healthy)    5432/tcp
# sci_backend     Up              0.0.0.0:8000->8000/tcp
# sci_frontend    Up              0.0.0.0:80->80/tcp
```

---

### 4. Acessar o sistema

| URL                          | O que e                        |
|------------------------------|--------------------------------|
| http://localhost             | Frontend React (interface)     |
| http://localhost/health      | Status da API                  |
| http://localhost:8000/docs   | Documentacao da API (Swagger)  |

Login em desenvolvimento (APP_ENV=development):
- usuario: `user` / senha: `user`
- usuario: `admin` / senha: `admin123`

---

### 5. Comandos uteis no dia a dia

```powershell
# Ver logs em tempo real
docker compose logs -f

# Ver logs so do backend
docker compose logs -f backend

# Parar tudo (dados sao preservados)
docker compose down

# Parar e APAGAR os dados do banco (cuidado!)
docker compose down -v

# Reiniciar apenas o backend (apos mudancas)
docker compose restart backend

# Entrar no terminal do container do backend
docker compose exec backend sh

# Acessar o banco de dados pelo terminal
docker compose exec postgres psql -U sci_user -d contrato_impressoras

# Reconstruir apos mudancas no codigo
docker compose up --build -d
```

---

## Levar o projeto para o trabalho

### Opcao 1 — Copiar os arquivos (mais simples)

1. Copie a pasta do projeto para um pendrive ou envie por rede
2. No computador do trabalho, instale o Docker Desktop
3. Crie o `.env` com as configuracoes corretas (AD do trabalho)
4. Execute `docker compose up --build -d`

### Opcao 2 — Exportar as imagens ja buildadas (sem precisar rebuildar)

No computador de casa (onde ja fez o build):

```powershell
# Salva as imagens em arquivos .tar
docker save sci-backend  -o sci-backend.tar
docker save sci-frontend -o sci-frontend.tar

# Compacta tudo
Compress-Archive -Path sci-backend.tar, sci-frontend.tar, docker-compose.yml, .env -DestinationPath sci-imagens.zip
```

No computador do trabalho:

```powershell
# Carrega as imagens salvas
docker load -i sci-backend.tar
docker load -i sci-frontend.tar

# Sobe o sistema (sem precisar buildar)
docker compose up -d
```

### Opcao 3 — Usar um registro privado (avancado)

Se sua organizacao tiver um registro Docker interno (Harbor, GitLab Registry, etc.),
voce pode fazer push das imagens para la e pull no trabalho.

---

## Configuracao para o trabalho (com AD)

Quando estiver no trabalho com acesso ao Active Directory,
altere o `.env` para usar autenticacao real:

```env
APP_ENV=production
DEBUG=false
AD_SERVER=10.10.10.10
AD_PORT=389
AD_DOMAIN=organizacao.mil.br
AD_BASE_DN=DC=organizacao,DC=mil,DC=br
AD_BIND_USER=CN=svc-sci,OU=Servicos,DC=organizacao,DC=mil,DC=br
AD_BIND_PASSWORD=SenhaDaContaDeServico
```

Depois reinicie apenas o backend:
```powershell
docker compose restart backend
```

---

## Atualizando o sistema apos mudancas no codigo

```powershell
# Recria apenas os containers que mudaram
docker compose up --build -d

# Se quiser forcar rebuild completo (limpa cache do Docker)
docker compose build --no-cache
docker compose up -d
```

---

## Solucao de problemas

**Container backend nao sobe:**
```powershell
docker compose logs backend
# Verifique erros de conexao com o banco ou variaveis de ambiente
```

**Pagina em branco no frontend:**
```powershell
docker compose logs frontend
# Verifique se o nginx.conf esta correto
```

**Banco de dados nao inicializa:**
```powershell
docker compose logs postgres
# Verifique as variaveis POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
```

**Porta 80 ja em uso:**
Altere a porta no docker-compose.yml:
```yaml
frontend:
  ports:
    - "8080:80"   # acesse em http://localhost:8080
```
