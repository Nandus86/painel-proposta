from pydantic import BaseModel, ConfigDict
from typing import Optional


class SistemaConfigBase(BaseModel):
    openrouter_key: Optional[str] = None
    openrouter_model: Optional[str] = None
    uazapi_base_url: Optional[str] = None
    uazapi_admin_token: Optional[str] = None


class SistemaConfigUpdate(BaseModel):
    openrouter_key: Optional[str] = None
    openrouter_model: Optional[str] = None
    uazapi_base_url: Optional[str] = None
    uazapi_admin_token: Optional[str] = None


class SistemaConfigResponse(BaseModel):
    has_openrouter_key: bool
    openrouter_model: str
    uazapi_base_url: Optional[str] = None
    has_uazapi_admin_token: bool = False

    model_config = ConfigDict(from_attributes=True)
