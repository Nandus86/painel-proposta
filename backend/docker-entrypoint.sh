#!/bin/sh
set -e

# Migrações automáticas na subida (desative com RUN_MIGRATIONS=false se rodar mais de uma réplica)
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "[entrypoint] Aplicando migrações do banco..."
    alembic upgrade head
fi

# Permite rodar comandos avulsos: docker compose run --rm backend python -m scripts.create_superadmin ...
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

echo "[entrypoint] Iniciando API com ${WEB_CONCURRENCY:-2} worker(s)..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${WEB_CONCURRENCY:-2}" \
    --proxy-headers \
    --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-*}" \
    --no-server-header
