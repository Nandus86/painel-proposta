from pydantic import BaseModel
from datetime import datetime
import uuid
from typing import Optional


class ModeloPropostaBase(BaseModel):
    titulo: str
    conteudo: str


class ModeloPropostaCreate(ModeloPropostaBase):
    pass


class ModeloPropostaUpdate(BaseModel):
    titulo: Optional[str] = None
    conteudo: Optional[str] = None


class ModeloPropostaResponse(ModeloPropostaBase):
    id: uuid.UUID
    empresa_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
