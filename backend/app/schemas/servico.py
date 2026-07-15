from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.servico import TipoServico
from app.schemas.categoria import CategoriaResponse


class ServicoBase(BaseModel):
    categoria_id: Optional[UUID] = None
    tipo: TipoServico = TipoServico.SERVICO
    nome: str = Field(..., max_length=200)
    descricao_padrao: Optional[str] = None
    instrucoes_ia: Optional[str] = None
    preco_base: float = Field(0.0, ge=0)
    custo_base: float = Field(0.0, ge=0)
    ativo: bool = True


class ServicoCreate(ServicoBase):
    pass


class ServicoUpdate(BaseModel):
    categoria_id: Optional[UUID] = None
    tipo: Optional[TipoServico] = None
    nome: Optional[str] = Field(None, max_length=200)
    descricao_padrao: Optional[str] = None
    instrucoes_ia: Optional[str] = None
    preco_base: Optional[float] = Field(None, ge=0)
    custo_base: Optional[float] = Field(None, ge=0)
    ativo: Optional[bool] = None


class ServicoResponse(ServicoBase):
    id: UUID
    empresa_id: UUID
    created_at: datetime
    updated_at: datetime
    categoria: Optional[CategoriaResponse] = None

    model_config = {"from_attributes": True}


class ServicoListResponse(BaseModel):
    items: List[ServicoResponse]
    total: int
    skip: int
    limit: int
