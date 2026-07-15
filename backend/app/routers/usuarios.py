import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.usuario import Usuario, UserRole
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse, UsuarioListResponse
from app.core.dependencies import get_current_user, require_admin
from app.core.security import get_password_hash

router = APIRouter(prefix="/api/usuarios", tags=["Usuários"])


@router.get("", response_model=UsuarioListResponse)
async def list_usuarios(
    search: str = Query(None, description="Buscar por nome ou email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List users from the same company."""
    query = select(Usuario).where(Usuario.empresa_id == current_user.empresa_id)

    if search:
        query = query.where(
            (Usuario.nome.ilike(f"%{search}%")) | (Usuario.email.ilike(f"%{search}%"))
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    result = await db.execute(
        query.order_by(Usuario.nome).offset(skip).limit(limit)
    )
    usuarios = result.scalars().all()

    return UsuarioListResponse(
        items=[
            UsuarioResponse(
                id=str(u.id),
                empresa_id=str(u.empresa_id),
                nome=u.nome,
                email=u.email,
                cargo=u.cargo,
                telefone=u.telefone,
                role=u.role.value,
                ativo=u.ativo,
                ultimo_login=u.ultimo_login,
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
            for u in usuarios
        ],
        total=total,
    )


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    data: UsuarioCreate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user. Admin only."""
    # Check email uniqueness
    existing = await db.execute(
        select(Usuario).where(Usuario.email == data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já cadastrado",
        )

    usuario = Usuario(
        empresa_id=current_user.empresa_id,
        nome=data.nome,
        email=data.email,
        senha_hash=get_password_hash(data.senha),
        cargo=data.cargo,
        telefone=data.telefone,
        role=UserRole(data.role),
    )
    db.add(usuario)
    await db.flush()
    await db.refresh(usuario)

    return UsuarioResponse(
        id=str(usuario.id),
        empresa_id=str(usuario.empresa_id),
        nome=usuario.nome,
        email=usuario.email,
        cargo=usuario.cargo,
        telefone=usuario.telefone,
        role=usuario.role.value,
        ativo=usuario.ativo,
        ultimo_login=usuario.ultimo_login,
        created_at=usuario.created_at,
        updated_at=usuario.updated_at,
    )


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(
    usuario_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user details."""
    result = await db.execute(
        select(Usuario).where(
            Usuario.id == uuid.UUID(usuario_id),
            Usuario.empresa_id == current_user.empresa_id,
        )
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return UsuarioResponse(
        id=str(usuario.id),
        empresa_id=str(usuario.empresa_id),
        nome=usuario.nome,
        email=usuario.email,
        cargo=usuario.cargo,
        telefone=usuario.telefone,
        role=usuario.role.value,
        ativo=usuario.ativo,
        ultimo_login=usuario.ultimo_login,
        created_at=usuario.created_at,
        updated_at=usuario.updated_at,
    )


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(
    usuario_id: str,
    data: UsuarioUpdate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user. Admin only."""
    result = await db.execute(
        select(Usuario).where(
            Usuario.id == uuid.UUID(usuario_id),
            Usuario.empresa_id == current_user.empresa_id,
        )
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    update_data = data.model_dump(exclude_unset=True)

    if "senha" in update_data:
        update_data["senha_hash"] = get_password_hash(update_data.pop("senha"))

    if "role" in update_data:
        update_data["role"] = UserRole(update_data["role"])

    for field, value in update_data.items():
        setattr(usuario, field, value)

    await db.flush()
    await db.refresh(usuario)

    return UsuarioResponse(
        id=str(usuario.id),
        empresa_id=str(usuario.empresa_id),
        nome=usuario.nome,
        email=usuario.email,
        cargo=usuario.cargo,
        telefone=usuario.telefone,
        role=usuario.role.value,
        ativo=usuario.ativo,
        ultimo_login=usuario.ultimo_login,
        created_at=usuario.created_at,
        updated_at=usuario.updated_at,
    )


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_usuario(
    usuario_id: str,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate user (soft delete). Admin only."""
    if str(current_user.id) == usuario_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode desativar seu próprio usuário",
        )

    result = await db.execute(
        select(Usuario).where(
            Usuario.id == uuid.UUID(usuario_id),
            Usuario.empresa_id == current_user.empresa_id,
        )
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    usuario.ativo = False
    await db.flush()
