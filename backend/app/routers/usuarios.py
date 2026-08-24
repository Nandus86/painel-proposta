import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.usuario import Usuario, UserRole
from app.models.plano import Plano
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    UsuarioListResponse,
    UsuarioQuotaResponse,
)
from app.core.dependencies import get_current_user, require_admin, verificar_limite_usuarios
from app.core.security import get_password_hash

router = APIRouter(prefix="/api/usuarios", tags=["Usuários"])


def to_usuario_response(u: Usuario) -> UsuarioResponse:
    return UsuarioResponse(
        id=str(u.id),
        empresa_id=str(u.empresa_id),
        nome=u.nome,
        email=u.email,
        cargo=u.cargo,
        telefone=u.telefone,
        role=u.role.value if hasattr(u.role, "value") else str(u.role),
        ativo=u.ativo,
        is_superuser=getattr(u, "is_superuser", False),
        ultimo_login=u.ultimo_login,
        created_at=u.created_at,
        updated_at=u.updated_at,
    )


@router.get("/quota", response_model=UsuarioQuotaResponse)
async def get_usuario_quota(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna o uso atual de usuários e a capacidade máxima do plano da empresa."""
    plano_slug = (current_user.empresa.plano or "gratuito").lower().strip()
    plano = await db.get(Plano, plano_slug)

    total_query = select(func.count(Usuario.id)).where(Usuario.empresa_id == current_user.empresa_id)
    ativos_query = select(func.count(Usuario.id)).where(
        Usuario.empresa_id == current_user.empresa_id,
        Usuario.ativo == True,
    )
    inativos_query = select(func.count(Usuario.id)).where(
        Usuario.empresa_id == current_user.empresa_id,
        Usuario.ativo == False,
    )

    total = await db.scalar(total_query) or 0
    ativos = await db.scalar(ativos_query) or 0
    inativos = await db.scalar(inativos_query) or 0

    max_usuarios = plano.max_usuarios if plano else 1
    plano_nome = plano.nome if plano else plano_slug.capitalize()
    pode_adicionar = max_usuarios is None or ativos < max_usuarios

    return UsuarioQuotaResponse(
        total=total,
        ativos=ativos,
        inativos=inativos,
        max_usuarios=max_usuarios,
        plano_slug=plano_slug,
        plano_nome=plano_nome,
        pode_adicionar=pode_adicionar,
    )


@router.get("", response_model=UsuarioListResponse)
async def list_usuarios(
    search: Optional[str] = Query(None, description="Buscar por nome ou email"),
    role: Optional[str] = Query(None, description="Filtrar por permissão"),
    status: Optional[str] = Query(None, description="Filtrar por status: all, active, inactive"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List users from the same company with filters."""
    query = select(Usuario).where(Usuario.empresa_id == current_user.empresa_id)

    if search and search.strip():
        s = search.strip()
        query = query.where(
            (Usuario.nome.ilike(f"%{s}%")) | (Usuario.email.ilike(f"%{s}%")) | (Usuario.cargo.ilike(f"%{s}%"))
        )

    if role and role in ["admin", "gerente", "vendedor"]:
        query = query.where(Usuario.role == UserRole(role))

    if status == "active":
        query = query.where(Usuario.ativo == True)
    elif status == "inactive":
        query = query.where(Usuario.ativo == False)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    result = await db.execute(
        query.order_by(Usuario.ativo.desc(), Usuario.nome.asc()).offset(skip).limit(limit)
    )
    usuarios = result.scalars().all()

    return UsuarioListResponse(
        items=[to_usuario_response(u) for u in usuarios],
        total=total,
    )


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    data: UsuarioCreate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _limit: None = Depends(verificar_limite_usuarios),
):
    """Create a new user. Admin only."""
    email_clean = data.email.strip().lower()
    # Check email uniqueness across all users
    existing = await db.execute(
        select(Usuario).where(Usuario.email == email_clean)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado no sistema.",
        )

    role_val = data.role.strip().lower()
    if role_val not in ["admin", "gerente", "vendedor"]:
        role_val = "vendedor"

    usuario = Usuario(
        empresa_id=current_user.empresa_id,
        nome=data.nome.strip(),
        email=email_clean,
        senha_hash=get_password_hash(data.senha),
        cargo=data.cargo.strip() if data.cargo else None,
        telefone=data.telefone.strip() if data.telefone else None,
        role=UserRole(role_val),
        ativo=True,
    )
    db.add(usuario)
    await db.flush()
    await db.refresh(usuario)

    return to_usuario_response(usuario)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(
    usuario_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user details."""
    try:
        user_uuid = uuid.UUID(usuario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuário inválido")

    result = await db.execute(
        select(Usuario).where(
            Usuario.id == user_uuid,
            Usuario.empresa_id == current_user.empresa_id,
        )
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return to_usuario_response(usuario)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(
    usuario_id: str,
    data: UsuarioUpdate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user. Admin only."""
    try:
        user_uuid = uuid.UUID(usuario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuário inválido")

    result = await db.execute(
        select(Usuario).where(
            Usuario.id == user_uuid,
            Usuario.empresa_id == current_user.empresa_id,
        )
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    update_data = data.model_dump(exclude_unset=True)

    # Check email uniqueness if modified
    if "email" in update_data and update_data["email"]:
        email_clean = update_data["email"].strip().lower()
        update_data["email"] = email_clean
        existing = await db.scalar(
            select(Usuario).where(
                Usuario.email == email_clean,
                Usuario.id != user_uuid,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este e-mail já está sendo utilizado por outro usuário.",
            )

    # Check activation user limit if activating an inactive user
    if update_data.get("ativo") is True and not usuario.ativo:
        plano_slug = (current_user.empresa.plano or "gratuito").lower().strip()
        plano = await db.get(Plano, plano_slug)
        if plano and plano.max_usuarios is not None:
            count = await db.scalar(
                select(func.count(Usuario.id)).where(
                    Usuario.empresa_id == current_user.empresa_id,
                    Usuario.ativo == True,
                )
            )
            if count >= plano.max_usuarios:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Limite de {plano.max_usuarios} usuário(s) ativos atingido no plano {plano.nome}. Faça upgrade para ativar este usuário.",
                )

    if "senha" in update_data:
        senha_val = update_data.pop("senha")
        if senha_val and len(senha_val.strip()) > 0:
            update_data["senha_hash"] = get_password_hash(senha_val.strip())

    if "role" in update_data and update_data["role"]:
        role_val = str(update_data["role"]).strip().lower()
        if role_val in ["admin", "gerente", "vendedor"]:
            update_data["role"] = UserRole(role_val)
        else:
            update_data.pop("role")

    if "nome" in update_data and update_data["nome"]:
        update_data["nome"] = update_data["nome"].strip()

    if "cargo" in update_data and update_data["cargo"]:
        update_data["cargo"] = update_data["cargo"].strip()

    if "telefone" in update_data and update_data["telefone"]:
        update_data["telefone"] = update_data["telefone"].strip()

    for field, value in update_data.items():
        setattr(usuario, field, value)

    await db.flush()
    await db.refresh(usuario)

    return to_usuario_response(usuario)


@router.patch("/{usuario_id}/toggle-status", response_model=UsuarioResponse)
async def toggle_usuario_status(
    usuario_id: str,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Alterna o status de um usuário (ativo / inativo)."""
    try:
        user_uuid = uuid.UUID(usuario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuário inválido")

    if str(current_user.id) == usuario_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode desativar seu próprio usuário.",
        )

    result = await db.execute(
        select(Usuario).where(
            Usuario.id == user_uuid,
            Usuario.empresa_id == current_user.empresa_id,
        )
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    new_status = not usuario.ativo

    # If activating, check plan limit
    if new_status:
        plano_slug = (current_user.empresa.plano or "gratuito").lower().strip()
        plano = await db.get(Plano, plano_slug)
        if plano and plano.max_usuarios is not None:
            count = await db.scalar(
                select(func.count(Usuario.id)).where(
                    Usuario.empresa_id == current_user.empresa_id,
                    Usuario.ativo == True,
                )
            )
            if count >= plano.max_usuarios:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Limite de {plano.max_usuarios} usuário(s) ativos atingido no plano {plano.nome}. Faça upgrade para ativar este usuário.",
                )

    usuario.ativo = new_status
    await db.flush()
    await db.refresh(usuario)

    return to_usuario_response(usuario)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_usuario(
    usuario_id: str,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate user (soft delete). Admin only."""
    try:
        user_uuid = uuid.UUID(usuario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuário inválido")

    if str(current_user.id) == usuario_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode desativar seu próprio usuário.",
        )

    result = await db.execute(
        select(Usuario).where(
            Usuario.id == user_uuid,
            Usuario.empresa_id == current_user.empresa_id,
        )
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    usuario.ativo = False
    await db.flush()

