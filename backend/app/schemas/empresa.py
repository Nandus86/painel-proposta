from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
import uuid


class EmpresaBase(BaseModel):
    razao_social: str
    nome_fantasia: Optional[str] = None
    cnpj: str
    inscricao_estadual: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    observacoes: Optional[str] = None
    pais: Optional[str] = None
    fuso_horario: Optional[str] = None
    moeda: Optional[str] = None
    idioma: Optional[str] = None
    setor: Optional[str] = None
    cor_marca: Optional[str] = None
    subdominio: Optional[str] = None
    dominio_personalizado: Optional[str] = None
    whatsapp_conectado: bool = False
    telegram_conectado: bool = False
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    pagamento_modo_teste: bool = True
    prefixo_proposta: str = "PROP"
    validade_padrao_dias: int = 30
    modelo_proposta_padrao: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None

class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(BaseModel):
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    observacoes: Optional[str] = None
    pais: Optional[str] = None
    fuso_horario: Optional[str] = None
    moeda: Optional[str] = None
    idioma: Optional[str] = None
    setor: Optional[str] = None
    cor_marca: Optional[str] = None
    subdominio: Optional[str] = None
    dominio_personalizado: Optional[str] = None
    whatsapp_conectado: Optional[bool] = None
    telegram_conectado: Optional[bool] = None
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    pagamento_modo_teste: Optional[bool] = None
    prefixo_proposta: Optional[str] = None
    validade_padrao_dias: Optional[int] = None
    modelo_proposta_padrao: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None


class EmpresaAdminUpdate(BaseModel):
    plano: Optional[str] = None
    status_pagamento: Optional[str] = None
    ativo: Optional[bool] = None


class EmpresaResponse(EmpresaBase):
    id: uuid.UUID
    logo_url: Optional[str] = None
    has_smtp_password: bool = False
    plano: str = "gratuito"
    status_pagamento: str = "em_dia"
    ativo: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
