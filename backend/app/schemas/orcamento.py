from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.orcamento import StatusOrcamento


class ItemOrcamentoBase(BaseModel):
    servico_id: Optional[UUID] = None
    descricao: str
    quantidade: float = 1.0
    preco_unitario: float
    desconto: float = 0.0
    subtotal: float
    ordem: int = 0


class ItemOrcamentoCreate(ItemOrcamentoBase):
    pass


class ItemOrcamentoResponse(ItemOrcamentoBase):
    id: UUID
    orcamento_id: UUID

    model_config = {"from_attributes": True}


class OrcamentoBase(BaseModel):
    cliente_id: UUID
    titulo: str = Field(..., max_length=255)
    status: StatusOrcamento = StatusOrcamento.RASCUNHO
    data_validade: Optional[datetime] = None
    validade_dias: int = 15
    observacoes: Optional[str] = None
    condicoes_pagamento: Optional[str] = None


class OrcamentoCreate(OrcamentoBase):
    items: List[ItemOrcamentoCreate]


class OrcamentoUpdate(BaseModel):
    cliente_id: Optional[UUID] = None
    titulo: Optional[str] = Field(None, max_length=255)
    status: Optional[StatusOrcamento] = None
    data_validade: Optional[datetime] = None
    validade_dias: Optional[int] = None
    observacoes: Optional[str] = None
    condicoes_pagamento: Optional[str] = None
    items: Optional[List[ItemOrcamentoCreate]] = None


class OrcamentoResponse(OrcamentoBase):
    id: UUID
    empresa_id: UUID
    usuario_id: UUID
    numero: int
    valor_total: float
    data_emissao: datetime
    created_at: datetime
    updated_at: datetime
    visualizacoes: int
    token_publico: UUID
    assinatura_ip: Optional[str] = None
    assinatura_data: Optional[datetime] = None
    items: List[ItemOrcamentoResponse]

    model_config = {"from_attributes": True}


class OrcamentoList(BaseModel):
    items: List[OrcamentoResponse]
    total: int
    skip: int
    limit: int
