from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class CategoriaBase(BaseModel):
    nome: str = Field(..., max_length=100)
    descricao: Optional[str] = None
    ativa: bool = True


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=100)
    descricao: Optional[str] = None
    ativa: Optional[bool] = None


class CategoriaResponse(CategoriaBase):
    id: UUID
    empresa_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoriaListResponse(BaseModel):
    items: List[CategoriaResponse]
    total: int
    skip: int
    limit: int
