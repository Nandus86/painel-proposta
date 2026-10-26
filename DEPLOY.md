# Deploy em produção (VPS)

Guia para colocar o painel no ar numa VPS Linux com Docker. Tempo estimado: 20–30 minutos.

## Arquitetura

```
Internet ──► Caddy (HTTPS, opcional) ──► frontend (nginx: SPA + proxy /api) ──► backend (FastAPI) ──► Postgres
                                                                                   └─ volume "uploads" (logos)
```

- Só o nginx (ou o Caddy) fica exposto. API e banco ficam na rede interna do Docker.
- As migrações do banco rodam automaticamente sempre que o backend sobe.
- Logs de todos os containers são rotacionados (10 MB × 5 arquivos).

## 1. Requisitos

- VPS com Ubuntu 22.04/24.04 (ou Debian 12), **mínimo 2 GB de RAM** e 20 GB de disco.
- Um domínio, com um registro **A** apontando para o IP da VPS (ex.: `app.seudominio.com.br`).

## 2. Preparar o servidor

```bash
# Docker + plugin compose
curl -fsSL https://get.docker.com | sh

# Firewall: SSH, HTTP e HTTPS
sudo ufw allow OpenSSH && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw enable

# Código
sudo mkdir -p /opt/painel-proposta && sudo chown $USER /opt/painel-proposta
git clone https://github.com/Nandus86/painel-proposta.git /opt/painel-proposta
cd /opt/painel-proposta
```

## 3. Configurar o `.env`

```bash
cp .env.example .env
openssl rand -hex 32   # copie para SECRET_KEY
openssl rand -hex 24   # copie para POSTGRES_PASSWORD
nano .env
```

Campos obrigatórios:

| Variável | Exemplo | Observação |
|---|---|---|
| `SECRET_KEY` | (64 caracteres hex) | **Guarde uma cópia.** Ela também cifra senhas SMTP e tokens salvos no banco; trocá-la depois invalida esses dados. |
| `POSTGRES_PASSWORD` | (48 caracteres hex) | Use só letras e números. |
| `APP_DOMAIN` | `app.seudominio.com.br` | Domínio do certificado HTTPS. |
| `FRONTEND_URL` | `https://app.seudominio.com.br` | Base dos links enviados aos clientes. |
| `CORS_ORIGINS` | `https://app.seudominio.com.br` | Igual à `FRONTEND_URL`. |

A API **não sobe** em produção se a `SECRET_KEY` estiver vazia, com menos de 32 caracteres ou com um valor de exemplo.

**Recomendado — e-mail do sistema** (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`): é por ele que saem a recuperação de senha, o e-mail de boas-vindas e o aviso ao vendedor quando o cliente aceita uma proposta. Sem ele, "Esqueci minha senha" mostra uma mensagem de indisponível. Prefira um serviço transacional (Amazon SES, Brevo, Resend, Mailgun…) e configure SPF/DKIM do domínio remetente para não cair em spam.

## 4. Subir

### Opção A — HTTPS automático com Caddy (recomendado para VPS dedicada)

No `.env`, defina `FRONTEND_BIND=127.0.0.1:8080` e suba com o perfil `https`:

```bash
docker compose --profile https up -d --build
```

O Caddy emite e renova sozinho o certificado Let's Encrypt. O DNS precisa já estar apontando para a VPS.

### Opção B — atrás de um proxy que você já usa (Traefik, Nginx Proxy Manager, Cloudflare Tunnel…)

Deixe `FRONTEND_BIND=80` (ou outra porta) e suba sem o perfil:

```bash
docker compose up -d --build
```

Aponte o seu proxy para essa porta. Se usar Portainer/Easypanel e o serviço da API tiver outro nome, ajuste `BACKEND_UPSTREAM` no serviço `frontend` (padrão: `backend:8000`).

### Verificar

```bash
docker compose ps                        # todos "healthy"
curl -s https://app.seudominio.com.br/api/health
docker compose logs -f backend           # Ctrl+C para sair
```

## 5. Primeiro acesso

Crie o super administrador (a senha é pedida no terminal):

```bash
docker compose exec backend python -m scripts.create_superadmin --email voce@seudominio.com.br --nome "Seu Nome"
```

Entre no painel com esse usuário e, em **Super Admin → Configurações**:

1. Cadastre a chave do **OpenRouter** e o modelo de IA (sem isso, a geração de texto por IA fica desativada com uma mensagem amigável).
2. Revise os **planos** (preços e limites).
3. Se for usar WhatsApp via Uazapi, cadastre a URL e o admin token.

Rotinas automáticas (ligadas por padrão, `JOBS_ENABLED`): a cada hora a API marca como vencidos os documentos **enviados** que passaram da validade e avisa o vendedor, no sino do painel, quando faltam `AVISO_VENCIMENTO_DIAS` dias para vencer. O vendedor também é avisado quando o cliente abre o link pela primeira vez e quando aceita.

Cada empresa cliente se cadastra em `/register` e configura o próprio SMTP no assistente inicial ou em **Configurações** (porta 465 = SSL; 587 = STARTTLS).

## 6. Backups

```bash
chmod +x deploy/backup.sh
./deploy/backup.sh          # gera backups/db-AAAAMMDD-HHMMSS.dump e uploads-*.tar.gz
```

Agende diariamente (`crontab -e`):

```
0 3 * * * cd /opt/painel-proposta && ./deploy/backup.sh >> backups/backup.log 2>&1
```

Os arquivos ficam na própria VPS: **copie-os para fora dela** (S3, Backblaze, Google Drive via rclone…). Guarde também o `.env`.

Restaurar:

```bash
docker compose exec -T db pg_restore -U painel -d painel_proposta --clean --if-exists < backups/db-XXXX.dump
docker compose exec -T backend tar -xzf - -C /app < backups/uploads-XXXX.tar.gz
```

## 7. Atualizar a versão

```bash
cd /opt/painel-proposta
./deploy/backup.sh
git pull
docker compose --profile https up -d --build   # ou sem --profile https, conforme a opção usada
```

As migrações rodam sozinhas na subida do backend.

## 8. Operação

| Tarefa | Comando |
|---|---|
| Logs da API | `docker compose logs -f --tail=200 backend` |
| Reiniciar a API | `docker compose restart backend` |
| Redefinir senha de um usuário | `docker compose exec backend python -m scripts.reset_password --email usuario@empresa.com` |
| Console do banco | `docker compose exec db psql -U painel -d painel_proposta` |

## Notas de segurança

- **Rate limiting** no nginx: login/cadastro/refresh limitados a 10 req/min por IP (com rajada de 10); links públicos a 60 req/min.
- **Cloudflare com proxy laranja direto no nginx**: o nginx só confia em `X-Forwarded-For` vindo de redes privadas. Para registrar o IP real dos clientes, adicione as faixas da Cloudflare com `set_real_ip_from` em `frontend/templates/default.conf.template` e troque `real_ip_header` para `CF-Connecting-IP`.
- **Subdomínio por empresa** (`empresa.seudominio.com.br`): exige DNS wildcard `*.seudominio.com.br` e certificado wildcard (desafio DNS). Até configurar isso, mantenha `PUBLIC_LINKS_USE_TENANT_DOMAIN=false`: os links usam a `FRONTEND_URL`.
- **Mais de uma réplica da API**: defina `RUN_MIGRATIONS=false` nas réplicas extras e rode as migrações uma única vez (`docker compose run --rm backend alembic upgrade head`).
- A documentação interativa da API (`/api/docs`) fica desligada em produção.
