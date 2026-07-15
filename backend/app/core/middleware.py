from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.models.empresa import Empresa
from app.config import settings


class DomainResolutionMiddleware:
    def __init__(self, async_session_factory: async_sessionmaker[AsyncSession]):
        self.async_session_factory = async_session_factory

    async def __call__(self, request: Request, call_next):
        host = request.headers.get("host", "").split(":")[0].lower()

        base_domain = getattr(settings, "BASE_DOMAIN", "painelproposta.com")

        if host == "localhost" or host == "127.0.0.1":
            request.state.empresa_id = None
            request.state.resolved_domain = False
            return await call_next(request)

        empresa_id = None
        resolved_domain = False

        if host.endswith(f".{base_domain}"):
            subdominio = host[: -len(f".{base_domain}")]
            if subdominio and subdominio != "www":
                async with self.async_session_factory() as db:
                    result = await db.execute(
                        select(Empresa).where(Empresa.subdominio == subdominio)
                    )
                    empresa = result.scalar_one_or_none()
                    if empresa and empresa.ativo:
                        empresa_id = str(empresa.id)
                        resolved_domain = True
        else:
            async with self.async_session_factory() as db:
                result = await db.execute(
                    select(Empresa).where(Empresa.dominio_personalizado == host)
                )
                empresa = result.scalar_one_or_none()
                if empresa and empresa.ativo:
                    empresa_id = str(empresa.id)
                    resolved_domain = True

        request.state.empresa_id = empresa_id
        request.state.resolved_domain = resolved_domain

        response = await call_next(request)
        return response
