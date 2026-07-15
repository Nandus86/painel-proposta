from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.usuario import Usuario
from app.models.sistema_config import SistemaConfig
from app.schemas.sistema_config import SistemaConfigUpdate, SistemaConfigResponse
from app.core.dependencies import require_superuser
from app.core.security import encrypt_data, decrypt_data

router = APIRouter(
    prefix="/api/admin/config",
    tags=["admin_config"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=SistemaConfigResponse)
async def get_config(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_superuser)
):
    result = await db.execute(select(SistemaConfig))
    config = result.scalar_one_or_none()
    if not config:
        config = SistemaConfig(id=1)
        db.add(config)
        await db.commit()
        await db.refresh(config)
        
    return SistemaConfigResponse(
        has_openrouter_key=config.has_openrouter_key,
        openrouter_model=config.openrouter_model
    )

@router.put("", response_model=SistemaConfigResponse)
async def update_config(
    config_data: SistemaConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_superuser)
):
    result = await db.execute(select(SistemaConfig))
    config = result.scalar_one_or_none()
    if not config:
        config = SistemaConfig(id=1)
        db.add(config)

    update_dict = config_data.model_dump(exclude_unset=True)
    
    if "openrouter_key" in update_dict:
        key_val = update_dict["openrouter_key"]
        if key_val:
            config.openrouter_key = encrypt_data(key_val)
        else:
            config.openrouter_key = None
            
    if "openrouter_model" in update_dict:
        config.openrouter_model = update_dict["openrouter_model"]

    await db.commit()
    await db.refresh(config)
    
    return SistemaConfigResponse(
        has_openrouter_key=config.has_openrouter_key,
        openrouter_model=config.openrouter_model
    )
