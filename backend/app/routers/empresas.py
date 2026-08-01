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
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate, EmpresaResponse, EmpresaAdminUpdate, DominioSetup, DominioVerifyResponse
from app.schemas.usuario import UsuarioCreate
from app.core.dependencies import get_current_user, require_admin, require_superuser
from app.core.security import get_password_hash
from app.models.usuario import UserRole
from app.config import settings
from app.services.storage import storage_service

router = APIRouter(prefix="/api/empresas", tags=["Empresas"])


@router.post("/me/setup-concluir")
async def concluir_setup(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    empresa.setup_concluido = True
    await db.commit()
    return {"message": "Setup concluído com sucesso"}



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

    await db.flush()
    await db.refresh(empresa)
    return EmpresaResponse.model_validate(empresa)


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

    return EmpresaResponse.model_validate(empresa)


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

    return EmpresaResponse.model_validate(empresa)


@router.post("/logo")
@router.post("/me/logo")
async def upload_empresa_logo(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Upload company logo image (MinIO or Local storage)."""
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo enviado deve ser uma imagem (PNG, JPG, SVG, WEBP, etc.)",
        )

    result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    logo_url = await storage_service.upload_file(file, folder="logos")
    empresa.logo_url = logo_url

    await db.flush()
    await db.refresh(empresa)

    return {"logo_url": logo_url}


@router.put("/me/dominio", response_model=EmpresaResponse)

async def configurar_dominio(
    data: DominioSetup,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    if data.subdominio is not None:
        sub = data.subdominio.strip().lower()
        if sub:
            import re
            if not re.match(r'^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$', sub):
                raise HTTPException(
                    status_code=400,
                    detail="Subdomínio inválido. Use apenas letras minúsculas, números e hífens (3-63 caracteres)."
                )
            if len(sub) < 3:
                raise HTTPException(status_code=400, detail="Subdomínio deve ter no mínimo 3 caracteres.")
            existing = await db.execute(
                select(Empresa).where(Empresa.subdominio == sub, Empresa.id != empresa.id)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Este subdomínio já está em uso.")
        empresa.subdominio = sub or None

    if data.dominio_personalizado is not None:
        dominio = data.dominio_personalizado.strip().lower()
        if dominio:
            from app.models.plano import Plano
            plano_obj = await db.get(Plano, empresa.plano)
            if not plano_obj or not plano_obj.permite_dominio_proprio:
                raise HTTPException(
                    status_code=400,
                    detail="Domínio personalizado requer plano Pro ou Empresarial."
                )
            import re
            if not re.match(r'^([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}$', dominio):
                raise HTTPException(status_code=400, detail="Domínio personalizado inválido.")
            existing = await db.execute(
                select(Empresa).where(Empresa.dominio_personalizado == dominio, Empresa.id != empresa.id)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Este domínio já está configurado por outra empresa.")
        empresa.dominio_personalizado = dominio or None

    await db.flush()
    await db.refresh(empresa)
    return EmpresaResponse.model_validate(empresa)


@router.post("/me/dominio/verificar", response_model=DominioVerifyResponse)
async def verificar_dominio(
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    if not empresa.dominio_personalizado:
        return DominioVerifyResponse(
            valido=False,
            detalhes="Nenhum domínio personalizado configurado."
        )

    dominio = empresa.dominio_personalizado
    base_domain = settings.BASE_DOMAIN

    return DominioVerifyResponse(
        valido=False,
        detalhes="Verificação manual de DNS necessária.",
        registros_esperados=[
            {
                "tipo": "CNAME",
                "host": dominio,
                "valor": base_domain,
                "descricao": "Aponte seu domínio via CNAME para o domínio base do Painel Proposta."
            },
            {
                "tipo": "TXT",
                "host": f"_painel.{dominio}",
                "valor": f"painel-verify={empresa.id}",
                "descricao": "Registro TXT opcional para verificação de propriedade."
            }
        ]
    )


@router.post("/me/smtp/testar")
async def testar_smtp(
    data: EmpresaUpdate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.services.email import send_email_sync
    from asyncio import get_event_loop

    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    smtp_host = data.smtp_host or empresa.smtp_host
    smtp_port = data.smtp_port or empresa.smtp_port
    smtp_user = data.smtp_user or empresa.smtp_user

    if not smtp_host or not smtp_port or not smtp_user:
        raise HTTPException(status_code=400, detail="Preencha todos os campos SMTP")

    from app.core.security import encrypt_data, decrypt_data
    pwd_to_use = None
    if data.smtp_password:
        pwd_to_use = data.smtp_password
    elif empresa.smtp_password:
        pwd_to_use = decrypt_data(empresa.smtp_password)
    if not pwd_to_use:
        raise HTTPException(status_code=400, detail="Senha SMTP não configurada")

    test_empresa = Empresa(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=encrypt_data(pwd_to_use),
    )

    loop = get_event_loop()
    await loop.run_in_executor(
        None,
        send_email_sync,
        test_empresa,
        current_user.email,
        f"Teste SMTP - {settings.APP_NAME}",
        "<h2>Teste de envio bem-sucedido!</h2><p>Se você está lendo isso, sua configuração SMTP está funcionando.</p>",
    )
    return {"message": "E-mail de teste enviado. Verifique sua caixa de entrada."}


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
