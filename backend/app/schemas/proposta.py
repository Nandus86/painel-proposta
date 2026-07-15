from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.proposta import StatusProposta


class ItemPropostaBase(BaseModel):
    servico_id: Optional[UUID] = None
    descricao: str
    quantidade: float = 1.0
    preco_unitario: float
    desconto: float = 0.0
    subtotal: float
    ordem: int = 0


class ItemPropostaCreate(ItemPropostaBase):
    pass


class ItemPropostaResponse(ItemPropostaBase):
    id: UUID
    proposta_id: UUID

    model_config = {"from_attributes": True}


class PropostaBase(BaseModel):
    cliente_id: UUID
    titulo: str = Field(..., max_length=255)
    status: StatusProposta = StatusProposta.RASCUNHO
    data_validade: Optional[datetime] = None
    validade_dias: int = 15
    observacoes: Optional[str] = None
    condicoes_pagamento: Optional[str] = None


class PropostaCreate(PropostaBase):
    items: List[ItemPropostaCreate]


class PropostaUpdate(BaseModel):
    cliente_id: Optional[UUID] = None
    titulo: Optional[str] = Field(None, max_length=255)
    status: Optional[StatusProposta] = None
    data_validade: Optional[datetime] = None
    validade_dias: Optional[int] = None
    observacoes: Optional[str] = None
    condicoes_pagamento: Optional[str] = None
    items: Optional[List[ItemPropostaCreate]] = None


class PropostaResponse(PropostaBase):
    id: UUID
    empresa_id: UUID
    usuario_id: UUID
    numero: int
    valor_total: float
    data_emissao: datetime
    created_at: datetime
    updated_at: datetime
    token_publico: UUID
    items: List[ItemPropostaResponse]

    model_config = {"from_attributes": True}


class PropostaList(BaseModel):
    id: UUID
    numero: int
    titulo: str
    cliente_nome: str
    status: StatusProposta
    valor_total: float
    data_emissao: datetime
    data_validade: Optional[datetime] = None
    token_publico: UUID

    model_config = {"from_attributes": True}
