#!/bin/sh
# Backup do banco e dos arquivos enviados (logos).
# Uso:  ./deploy/backup.sh            (guarda em ./backups, mantém os últimos 14 dias)
# Cron diário às 3h:  0 3 * * * cd /opt/painel-proposta && ./deploy/backup.sh >> backups/backup.log 2>&1
set -eu

cd "$(dirname "$0")/.."
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
STAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BACKUP_DIR"

# Lê usuário/banco do .env (com padrão)
POSTGRES_USER="$(grep -E '^POSTGRES_USER=' .env | cut -d= -f2- || true)"
POSTGRES_DB="$(grep -E '^POSTGRES_DB=' .env | cut -d= -f2- || true)"
POSTGRES_USER="${POSTGRES_USER:-painel}"
POSTGRES_DB="${POSTGRES_DB:-painel_proposta}"

echo "[$(date)] Backup do banco..."
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner \
    > "$BACKUP_DIR/db-$STAMP.dump"

echo "[$(date)] Backup dos uploads..."
docker compose exec -T backend tar -czf - -C /app uploads > "$BACKUP_DIR/uploads-$STAMP.tar.gz"

find "$BACKUP_DIR" -name 'db-*.dump' -mtime +"$RETENTION_DAYS" -delete
find "$BACKUP_DIR" -name 'uploads-*.tar.gz' -mtime +"$RETENTION_DAYS" -delete

echo "[$(date)] Concluído: $BACKUP_DIR/db-$STAMP.dump e uploads-$STAMP.tar.gz"
