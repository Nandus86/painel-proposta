import os
import shutil
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate, EmpresaResponse, EmpresaAdminUpdate
from app.schemas.usuario import UsuarioCreate
from app.core.dependencies import get_current_user, require_admin, require_superuser
from app.core.security import get_password_hash
from app.models.usuario import UserRole

router = APIRouter(prefix="/api/empresas", tags=["Empresas"])


@router.post("/setup", response_model=EmpresaResponse, status_code=status.HTTP_201_CREATED)
async def setup_empresa(
    data: EmpresaCreate,
    admin_email: str,
    admin_senha: str,
    admin_nome: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Initial setup: Create company and first admin user.
    This endpoint is only available when no companies exist.
    """
    # Check if any company exists
    result = await db.execute(select(Empresa).limit(1))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setup já realizado. Use o login para acessar.",
        )

    # Create empresa
    empresa = Empresa(**data.model_dump())
    db.add(empresa)
    await db.flush()

    # Create admin user
    admin = Usuario(
        empresa_id=empresa.id,
        nome=admin_nome,
        email=admin_email,
        senha_hash=get_password_hash(admin_senha),
        role=UserRole.ADMIN,
        cargo="Administrador",
    )
    db.add(admin)

    return EmpresaResponse(
        id=str(empresa.id),
        razao_social=empresa.razao_social,
        nome_fantasia=empresa.nome_fantasia,
        cnpj=empresa.cnpj,
        inscricao_estadual=empresa.inscricao_estadual,
        email=empresa.email,
        telefone=empresa.telefone,
        endereco=empresa.endereco,
        cidade=empresa.cidade,
        estado=empresa.estado,
        cep=empresa.cep,
        observacoes=empresa.observacoes,
        prefixo_proposta=empresa.prefixo_proposta,
        validade_padrao_dias=empresa.validade_padrao_dias,
        logo_url=empresa.logo_url,
        has_smtp_password=empresa.has_smtp_password,
        smtp_host=empresa.smtp_host,
        smtp_port=empresa.smtp_port,
        smtp_user=empresa.smtp_user,
        created_at=empresa.created_at,
        updated_at=empresa.updated_at,
    )


@router.get("/me", response_model=EmpresaResponse)
async def get_my_empresa(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's company."""
    result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    return EmpresaResponse(
        id=str(empresa.id),
        razao_social=empresa.razao_social,
        nome_fantasia=empresa.nome_fantasia,
        cnpj=empresa.cnpj,
        inscricao_estadual=empresa.inscricao_estadual,
        email=empresa.email,
        telefone=empresa.telefone,
        endereco=empresa.endereco,
        cidade=empresa.cidade,
        estado=empresa.estado,
        cep=empresa.cep,
        observacoes=empresa.observacoes,
        prefixo_proposta=empresa.prefixo_proposta,
        validade_padrao_dias=empresa.validade_padrao_dias,
        logo_url=empresa.logo_url,
        has_smtp_password=empresa.has_smtp_password,
        smtp_host=empresa.smtp_host,
        smtp_port=empresa.smtp_port,
        smtp_user=empresa.smtp_user,
        created_at=empresa.created_at,
        updated_at=empresa.updated_at,
    )


@router.put("/me", response_model=EmpresaResponse)
async def update_my_empresa(
    data: EmpresaUpdate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's company. Admin only."""
    result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    update_data = data.model_dump(exclude_unset=True)


    if "smtp_password" in update_data:
        from app.core.security import encrypt_data
        smtp_pwd_val = update_data["smtp_password"]
        if smtp_pwd_val:
            update_data["smtp_password"] = encrypt_data(smtp_pwd_val)
        else:
            update_data["smtp_password"] = None

    for field, value in update_data.items():
        setattr(empresa, field, value)

    await db.flush()
    await db.refresh(empresa)

    return EmpresaResponse(
        id=str(empresa.id),
        razao_social=empresa.razao_social,
        nome_fantasia=empresa.nome_fantasia,
        cnpj=empresa.cnpj,
        inscricao_estadual=empresa.inscricao_estadual,
        email=empresa.email,
        telefone=empresa.telefone,
        endereco=empresa.endereco,
        cidade=empresa.cidade,
        estado=empresa.estado,
        cep=empresa.cep,
        observacoes=empresa.observacoes,
        prefixo_proposta=empresa.prefixo_proposta,
        validade_padrao_dias=empresa.validade_padrao_dias,
        logo_url=empresa.logo_url,
        has_smtp_password=empresa.has_smtp_password,
        smtp_host=empresa.smtp_host,
        smtp_port=empresa.smtp_port,
        smtp_user=empresa.smtp_user,
        created_at=empresa.created_at,
        updated_at=empresa.updated_at,
    )

@router.post("/logo", response_model=EmpresaResponse)
async def upload_logo(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Upload company logo."""
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="O arquivo deve ser uma imagem")

    file_extension = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join("uploads/logos", filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    empresa.logo_url = f"/uploads/logos/{filename}"
    await db.flush()
    await db.refresh(empresa)

    return EmpresaResponse.model_validate(empresa)

@router.get("/admin/todas", response_model=List[EmpresaResponse])
async def list_todas_empresas(
    current_user: Usuario = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """List all companies. Superuser only."""
    result = await db.execute(select(Empresa))
    empresas = result.scalars().all()
    return [EmpresaResponse.model_validate(e) for e in empresas]

@router.put("/admin/{id}/status", response_model=EmpresaResponse)
async def update_empresa_status(
    id: uuid.UUID,
    data: EmpresaAdminUpdate,
    current_user: Usuario = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Update company plan and status. Superuser only."""
    result = await db.execute(select(Empresa).where(Empresa.id == id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(empresa, field, value)

    await db.flush()
    await db.refresh(empresa)

    return EmpresaResponse.model_validate(empresa)
