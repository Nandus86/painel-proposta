from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import require_superuser
from app.core.security import encrypt_data
from app.database import get_db
from app.models.sistema_config import SistemaConfig
from app.models.usuario import Usuario
from app.schemas.sistema_config import SistemaConfigResponse, SistemaConfigUpdate

router = APIRouter(
    prefix="/api/admin/config",
    tags=["admin_config"],
    responses={404: {"description": "Not found"}},
)


def _serialize_config(config: SistemaConfig) -> SistemaConfigResponse:
    return SistemaConfigResponse(
        has_openrouter_key=config.has_openrouter_key,
        openrouter_model=config.openrouter_model,
        uazapi_base_url=config.uazapi_base_url or getattr(settings, "WHATSAPP_API_URL", None),
        has_uazapi_admin_token=config.has_uazapi_admin_token or bool(getattr(settings, "WHATSAPP_ADMIN_TOKEN", None)),
    )


@router.get("", response_model=SistemaConfigResponse)
async def get_config(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_superuser),
):
    config = await db.get(SistemaConfig, 1)
    if not config:
        config = SistemaConfig(id=1)
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return _serialize_config(config)


@router.put("", response_model=SistemaConfigResponse)
async def update_config(
    config_data: SistemaConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_superuser),
):
    config = await db.get(SistemaConfig, 1)
    if not config:
        config = SistemaConfig(id=1)
        db.add(config)

    update_dict = config_data.model_dump(exclude_unset=True)

    if "openrouter_key" in update_dict:
        key_val = update_dict["openrouter_key"]
        config.openrouter_key = encrypt_data(key_val) if key_val else None

    if "openrouter_model" in update_dict and update_dict["openrouter_model"] is not None:
        config.openrouter_model = update_dict["openrouter_model"]

    if "uazapi_base_url" in update_dict:
        url_val = (update_dict["uazapi_base_url"] or "").strip().rstrip("/")
        config.uazapi_base_url = url_val or None

    if "uazapi_admin_token" in update_dict:
        tok_val = (update_dict["uazapi_admin_token"] or "").strip()
        config.uazapi_admin_token = encrypt_data(tok_val) if tok_val else None

    await db.commit()
    await db.refresh(config)

    return _serialize_config(config)
