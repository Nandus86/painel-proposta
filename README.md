# Painel de Propostas

Plataforma multiempresa para criar, enviar e acompanhar **propostas comerciais e orçamentos**, com texto gerado por IA, PDF, link público com aceite eletrônico e envio por e-mail/WhatsApp.

- **Backend:** FastAPI · SQLAlchemy (async) · Alembic · PostgreSQL
- **Frontend:** Vue 3 · PrimeVue 4 · Pinia · Vite
- **Infra:** Docker Compose · nginx · Caddy (HTTPS opcional)

## Produção

Veja o guia passo a passo em **[DEPLOY.md](DEPLOY.md)**. Resumo:

```bash
cp .env.example .env    # preencha SECRET_KEY, POSTGRES_PASSWORD e os domínios
docker compose --profile https up -d --build
docker compose exec backend python -m scripts.create_superadmin --email voce@dominio.com
```

## Desenvolvimento local

```bash
# Banco
docker compose -f docker-compose.dev.yml up -d

# API (Python 3.12)
cd backend
python -m venv .venv && .venv/Scripts/activate   # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload                    # http://localhost:8000/api/docs

# Frontend (Node 22)
cd frontend
npm ci
npm run dev                                      # http://localhost:5173
```

### Testes

Os testes do backend usam um Postgres real (o schema do banco de teste é **apagado** a cada execução):

```bash
docker compose -f docker-compose.dev.yml exec db createdb -U postgres painel_proposta_test
cd backend
pip install -r requirements-dev.txt
python -m pytest -q
```

Para apontar para outro banco: `TEST_DATABASE_URL=postgresql+asyncpg://usuario:senha@host:5432/banco_de_teste`.
O GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml)) roda testes, `alembic check`, build do frontend e build das imagens Docker a cada push e pull request.

### Migrações

```bash
cd backend
alembic revision --autogenerate -m "descricao"   # revise o arquivo gerado antes de aplicar
alembic upgrade head
alembic check                                    # confirma que modelos e banco estão em sincronia
```

## Estrutura

```
backend/
  app/routers/documentos.py   rotas compartilhadas de propostas e orçamentos
  app/services/               PDF, e-mail, storage, links públicos, WhatsApp
  alembic/versions/           migrações
  scripts/                    create_superadmin, reset_password
frontend/
  src/views/                  telas
  templates/                  config do nginx (gerada por variáveis de ambiente)
deploy/                       Caddyfile e script de backup
```
