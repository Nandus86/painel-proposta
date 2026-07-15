import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.core.security import decode_token
from app.models.usuario import Usuario

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

    return user


# Aliases
get_current_active_user = get_current_user


async def require_admin(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """Dependency that requires admin role."""
    from app.models.usuario import UserRole
    # Compare with the enum member directly. Since UserRole inherits from str, 
    # this will work even if current_user.role is somehow a raw string 'admin'.
    if current_user.role != UserRole.ADMIN:
        print(f"DEBUG require_admin failed: user={current_user.email}, role={repr(current_user.role)}, type={type(current_user.role)}")
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
        print(f"DEBUG require_gerente_or_admin failed: user={current_user.email}, role={repr(current_user.role)}, type={type(current_user.role)}")
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
