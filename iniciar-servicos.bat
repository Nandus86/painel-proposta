@echo off
chcp 65001 >nul
echo ========================================================
echo       INICIANDO STACK PAINEL PROPOSTA + WHATSAPP
echo ========================================================
echo.

echo [1/3] Garantindo servico do WhatsApp (whatsmeow-basileia)...
docker compose -f D:\projetos\whatsmeow-basileia\docker-compose.yml up -d
if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Nao foi possivel iniciar via docker-compose do whatsmeow diretamente. Tentando iniciar containers existentes...
    docker start whatsmeow-app whatsmeow-rabbitmq whatsmeow-postgres whatsmeow-redis whatsmeow-minio 2>nul
)

echo [2/3] Iniciando Backend FastAPI (Porta 8001)...
start "Backend Painel Proposta :8001" cmd /k "cd /d %~dp0backend && .venv\Scripts\activate && uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

echo [3/3] Iniciando Frontend Vite (Porta 5173)...
start "Frontend Painel Proposta :5173" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================================
echo   Servicos iniciados com sucesso!
echo.
echo   - Frontend:      http://localhost:5173
echo   - Backend Docs:  http://localhost:8001/api/docs
echo   - WhatsApp API:  http://localhost:8080
echo ========================================================
pause
