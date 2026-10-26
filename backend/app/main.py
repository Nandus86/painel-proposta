import asyncio
import contextlib
import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging import setup_logging
from app.core.dependencies import get_current_user
from app.database import AsyncSessionLocal, engine, get_db
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.routers import (
    auth, empresas, usuarios, clientes, categorias, servicos, propostas, ai, modelos,
    public, dashboard, orcamentos, admin_config, superadmin, planos, whatsapp, notificacoes,
)
from app.services.notificacoes import loop_rotinas
from app.services.storage import storage_service

setup_logging()
logger = logging.getLogger("app")

os.makedirs("uploads/logos", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s v%s iniciando (ambiente=%s)", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    if settings.is_production and "localhost" in settings.FRONTEND_URL:
        logger.warning("FRONTEND_URL=%s: os links enviados aos clientes apontarão para localhost. Ajuste no .env.", settings.FRONTEND_URL)
    rotinas = asyncio.create_task(loop_rotinas(AsyncSessionLocal)) if settings.JOBS_ENABLED else None
    yield
    if rotinas:
        rotinas.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await rotinas
    await engine.dispose()
    logger.info("%s encerrado", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para criação e gestão de propostas comerciais com assistência de IA",
    lifespan=lifespan,
    # Documentação interativa só fora de produção
    docs_url=None if settings.is_production else "/api/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/api/openapi.json",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [{k: v for k, v in err.items() if k != "input"} for err in exc.errors()]
    return JSONResponse(status_code=422, content=jsonable_encoder({"detail": errors}))


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    logger.warning("IntegrityError em %s %s: %s", request.method, request.url.path, exc.orig)
    return JSONResponse(
        status_code=409,
        content={"detail": "Operação não permitida: o registro está em uso por outros dados ou já existe."},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor. Tente novamente em instantes."})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(empresas.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(categorias.router)
app.include_router(servicos.router)
app.include_router(propostas.router)
app.include_router(ai.router)
app.include_router(modelos.router)
app.include_router(public.router)
app.include_router(public.orcamento_router)
app.include_router(dashboard.router)
app.include_router(orcamentos.router)
app.include_router(admin_config.router)
app.include_router(superadmin.router)
app.include_router(planos.router)
app.include_router(whatsapp.router)
app.include_router(notificacoes.router)


# Arquivos enviados: nunca executam nada no navegador (defesa extra contra SVG/HTML malicioso)
_UPLOAD_HEADERS = {
    "Cache-Control": "public, max-age=86400",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; sandbox",
}


@app.get("/uploads/{path:path}")
async def get_uploaded_file(path: str):
    """Serve arquivos enviados a partir do disco local ou do MinIO."""
    safe_path = os.path.normpath(path).lstrip("/\\")
    local_file = os.path.join("uploads", safe_path)
    real_local = os.path.realpath(local_file)
    real_uploads = os.path.realpath("uploads")
    if not real_local.startswith(real_uploads + os.sep):
        return JSONResponse(status_code=403, content={"detail": "Acesso negado"})
    if os.path.isfile(real_local):
        return FileResponse(real_local, headers=_UPLOAD_HEADERS)

    content, content_type = await storage_service.get_file_content(safe_path.replace("\\", "/"))
    if content:
        return Response(content=content, media_type=content_type, headers=_UPLOAD_HEADERS)

    return JSONResponse(status_code=404, content={"detail": "Arquivo não encontrado"})


@app.get("/api/health")
async def health_check():
    """Health check usado pelo Docker/proxy: também verifica o banco."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check: banco indisponível")
        return JSONResponse(status_code=503, content={"status": "error", "database": "unavailable"})
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/api/setup/status")
async def setup_status(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Indica se o assistente de configuração inicial já foi concluído pela empresa."""
    result = await db.execute(select(Empresa.setup_concluido).where(Empresa.id == current_user.empresa_id))
    return {"setup_done": bool(result.scalar_one_or_none())}
