from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    cargo: Optional[str] = None
    telefone: Optional[str] = None
    role: str = "vendedor"


class UsuarioCreate(UsuarioBase):
    senha: str


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    cargo: Optional[str] = None
    telefone: Optional[str] = None
    role: Optional[str] = None
    ativo: Optional[bool] = None
    senha: Optional[str] = None


class UsuarioResponse(BaseModel):
    id: str
    empresa_id: str
    nome: str
    email: str
    cargo: Optional[str] = None
    telefone: Optional[str] = None
    role: str
    ativo: bool
    is_superuser: bool
    ultimo_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UsuarioListResponse(BaseModel):
    items: list[UsuarioResponse]
    total: int
