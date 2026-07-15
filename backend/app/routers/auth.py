from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, UserInfo, RegisterRequest
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.dependencies import get_current_user
from app.models.empresa import Empresa
from app.models.usuario import UserRole
import uuid

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user and create their company."""
    # Verifies if email exists
    result = await db.execute(
        select(Usuario).where(Usuario.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso.",
        )

    # Create a new Empresa with dummy unique data
    # setup_done will be based on filling other fields later
    dummy_cnpj = f"TMP-{str(uuid.uuid4())[:14]}"
    nova_empresa = Empresa(
        razao_social=f"Empresa de {data.nome}",
        cnpj=dummy_cnpj,
    )
    db.add(nova_empresa)
    await db.flush()

    # Create the Usuario
    novo_usuario = Usuario(
        empresa_id=nova_empresa.id,
        nome=data.nome,
        email=data.email,
        senha_hash=get_password_hash(data.senha),
        role=UserRole.ADMIN,
        cargo="Administrador",
    )
    db.add(novo_usuario)
    await db.commit()

    # Log in the user automatically
    access_token = create_access_token(
        data={"sub": str(novo_usuario.id), "empresa_id": str(nova_empresa.id), "role": novo_usuario.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(novo_usuario.id)}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    result = await db.execute(
        select(Usuario).where(Usuario.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.senha, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )

    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado. Contate o administrador.",
        )

    # Update last login
    user.ultimo_login = datetime.now(timezone.utc)

    access_token = create_access_token(
        data={"sub": str(user.id), "empresa_id": str(user.empresa_id), "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token."""
    payload = decode_token(data.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido",
        )

    user_id = payload.get("sub")
    result = await db.execute(
        select(Usuario).where(Usuario.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "empresa_id": str(user.empresa_id), "role": user.role.value}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: Usuario = Depends(get_current_user)):
    """Return current authenticated user info."""
    return UserInfo(
        id=str(current_user.id),
        nome=current_user.nome,
        email=current_user.email,
        cargo=current_user.cargo,
        role=current_user.role.value,
        empresa_id=str(current_user.empresa_id),
        empresa_nome=current_user.empresa.nome_fantasia or current_user.empresa.razao_social
        if current_user.empresa else None,
        empresa_cor_marca=current_user.empresa.cor_marca if current_user.empresa else None,
        is_superuser=current_user.is_superuser,
    )
