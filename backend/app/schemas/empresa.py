from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
import re
import uuid


# CNPJ provisório gerado no cadastro (o cliente preenche o real depois)
PLACEHOLDER_PREFIXES = ("TMP-", "ADM-")


def normalizar_documento(value: Optional[str]) -> Optional[str]:
    """Normaliza CNPJ/CPF para o formato com pontuação; retorna None se vazio."""
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if len(digits) == 14:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    if len(digits) == 11:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    raise ValueError("CNPJ/CPF inválido: informe 14 (CNPJ) ou 11 (CPF) dígitos.")


def documento_publico(value: Optional[str]) -> Optional[str]:
    """Documento para exibição: oculta o placeholder interno."""
    if not value or value.startswith(PLACEHOLDER_PREFIXES):
        return None
    return value


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
    uazapi_instance_id: Optional[str] = None
    whatsapp_numero: Optional[str] = None
    whatsapp_status: Optional[str] = None
    whatsapp_mensagem_padrao: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    pagamento_modo_teste: bool = True
    prefixo_proposta: str = "PROP"
    validade_padrao_dias: int = 30
    modelo_proposta_padrao: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    email_assunto_padrao: Optional[str] = None
    email_corpo_padrao: Optional[str] = None
    logo_url: Optional[str] = None

class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(BaseModel):
    razao_social: Optional[str] = Field(None, max_length=255)
    nome_fantasia: Optional[str] = Field(None, max_length=255)
    cnpj: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)

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
    whatsapp_conectado: Optional[bool] = None
    whatsapp_numero: Optional[str] = None
    whatsapp_status: Optional[str] = None
    whatsapp_mensagem_padrao: Optional[str] = None
    telegram_conectado: Optional[bool] = None
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    pagamento_modo_teste: Optional[bool] = None
    prefixo_proposta: Optional[str] = Field(None, max_length=10)
    validade_padrao_dias: Optional[int] = Field(None, ge=1, le=365)
    modelo_proposta_padrao: Optional[str] = None
    smtp_host: Optional[str] = Field(None, max_length=255)
    smtp_port: Optional[int] = Field(None, ge=1, le=65535)
    smtp_user: Optional[str] = Field(None, max_length=255)
    smtp_password: Optional[str] = None
    email_assunto_padrao: Optional[str] = Field(None, max_length=255)
    email_corpo_padrao: Optional[str] = None

    @field_validator("cnpj")
    @classmethod
    def _validar_cnpj(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.startswith(PLACEHOLDER_PREFIXES) or not v.strip():
            return None
        normalizar_documento(v)
        return v

    @field_validator("estado")
    @classmethod
    def _validar_estado(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().upper()[:2] if v else v

    @field_validator("cor_marca")
    @classmethod
    def _validar_cor(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.fullmatch(r"#?[0-9a-fA-F]{3,8}", v.strip()):
            raise ValueError("Cor inválida (use o formato hexadecimal, ex.: #4f46e5).")
        return v


class EmpresaAdminUpdate(BaseModel):
    plano: Optional[str] = None
    plano_solicitado: Optional[str] = None
    status_pagamento: Optional[str] = None
    ativo: Optional[bool] = None


class DominioSetup(BaseModel):
    subdominio: Optional[str] = None
    dominio_personalizado: Optional[str] = None


class DominioVerifyResponse(BaseModel):
    valido: bool
    detalhes: str
    registros_esperados: Optional[list[dict]] = None


class EmpresaResponse(EmpresaBase):
    id: uuid.UUID
    logo_url: Optional[str] = None
    has_smtp_password: bool = False
    has_stripe_secret_key: bool = False
    # Segredo nunca sai da API
    stripe_secret_key: Optional[str] = Field(None, exclude=True)
    plano: str = "gratuito"
    plano_solicitado: Optional[str] = None
    status_pagamento: str = "em_dia"
    ativo: bool = True
    setup_concluido: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
