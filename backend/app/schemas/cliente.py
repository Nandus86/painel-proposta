from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class ClienteBase(BaseModel):
    razao_social: str
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    cpf: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    contato_nome: Optional[str] = None
    contato_cargo: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    observacoes: Optional[str] = None


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    cpf: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    contato_nome: Optional[str] = None
    contato_cargo: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    observacoes: Optional[str] = None


class ClienteResponse(ClienteBase):
    id: str
    empresa_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClienteListResponse(BaseModel):
    items: list[ClienteResponse]
    total: int
    skip: int
    limit: int
