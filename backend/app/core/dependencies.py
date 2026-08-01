import uuid
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.core.security import decode_token
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)
security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """Dependency that validates JWT and returns the current user."""
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    result = await db.execute(
        select(Usuario)
        .where(Usuario.id == uuid.UUID(user_id))
        .options(selectinload(Usuario.empresa))
    )
    user = result.scalar_one_or_none()

    if user is None or not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo",
        )

    if user.empresa and not user.empresa.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Empresa bloqueada. Contate o administrador do sistema.",
        )

    return user


# Aliases
get_current_active_user = get_current_user


async def require_admin(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """Dependency that requires admin role."""
    from app.models.usuario import UserRole
    if current_user.role != UserRole.ADMIN:
        logger.debug(f"require_admin failed: user={current_user.email}, role={repr(current_user.role)}, type={type(current_user.role)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return current_user


async def require_gerente_or_admin(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """Dependency that requires gerente or admin role."""
    from app.models.usuario import UserRole
    if current_user.role not in (UserRole.ADMIN, UserRole.GERENTE):
        logger.debug(f"require_gerente_or_admin failed: user={current_user.email}, role={repr(current_user.role)}, type={type(current_user.role)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a gerentes e administradores",
        )
    return current_user

async def require_superuser(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """Dependency that requires superuser flag."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a super administradores do sistema",
        )
    return current_user


async def verificar_limite_propostas(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.plano import Plano
    from app.models.proposta import Proposta
    from datetime import datetime, timezone

    plano = await db.get(Plano, current_user.empresa.plano)
    if not plano or plano.max_propostas_mes is None:
        return

    inicio_mes = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    count = await db.scalar(
        select(func.count(Proposta.id)).where(
            Proposta.empresa_id == current_user.empresa_id,
            Proposta.created_at >= inicio_mes,
        )
    )
    if count >= plano.max_propostas_mes:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Limite de {plano.max_propostas_mes} propostas por mês atingido. Faça upgrade do seu plano.",
        )


async def verificar_limite_usuarios(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.plano import Plano
    from app.models.usuario import Usuario as UsuarioModel

    plano = await db.get(Plano, current_user.empresa.plano)
    if not plano or plano.max_usuarios is None:
        return

    count = await db.scalar(
        select(func.count(UsuarioModel.id)).where(
            UsuarioModel.empresa_id == current_user.empresa_id,
            UsuarioModel.ativo == True,
        )
    )
    if count >= plano.max_usuarios:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Limite de {plano.max_usuarios} usuários atingido. Faça upgrade do seu plano.",
        )
