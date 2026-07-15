from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, empresas, usuarios, clientes, categorias, servicos, propostas, ai, modelos, public, dashboard, orcamentos, admin_config
from app.models import Orcamento
from fastapi.staticfiles import StaticFiles
import os

# Create uploads directory if it doesn't exist
os.makedirs("uploads/logos", exist_ok=True)

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    print(f"[{settings.APP_NAME}] v{settings.APP_VERSION} starting...")
    yield
    print(f"[{settings.APP_NAME}] shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para criação e gestão de propostas comerciais com assistência de IA",
    lifespan=lifespan,
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation Error: {exc.errors()}")
    print(f"Body: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# CORS
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

# Mount Static Files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


from fastapi import Depends
from app.core.dependencies import get_current_user
from app.models.usuario import Usuario
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

@app.get("/api/setup/status")
async def setup_status(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if initial setup has been done for the user's company."""
    from sqlalchemy import select
    from app.models.empresa import Empresa

    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()

    setup_done = False
    # If the user completed the setup step 1, they would have provided a phone number 
    # or changed the company name from the dummy "Empresa de {nome}"
    if empresa and empresa.telefone:
        setup_done = True

    return {"setup_done": setup_done}
