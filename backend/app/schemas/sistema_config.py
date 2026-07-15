from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SistemaConfigBase(BaseModel):
    openrouter_key: Optional[str] = None
    openrouter_model: Optional[str] = None

class SistemaConfigUpdate(BaseModel):
    openrouter_key: Optional[str] = None
    openrouter_model: Optional[str] = None

class SistemaConfigResponse(BaseModel):
    has_openrouter_key: bool
    openrouter_model: str

    class Config:
        from_attributes = True
