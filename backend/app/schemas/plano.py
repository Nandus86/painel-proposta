from pydantic import BaseModel
from typing import Optional


class PlanoResponse(BaseModel):
    slug: str
    nome: str
    descricao: Optional[str] = None
    preco_mensal: Optional[float] = None
    preco_anual: Optional[float] = None
    moeda: str = "BRL"
    max_usuarios: Optional[int] = None
    max_propostas_mes: Optional[int] = None
    ai_credits_limit: int = 20
    permite_dominio_proprio: bool = False
    ordem: int = 0
    ativo: bool = True
    destaque: bool = False

    model_config = {"from_attributes": True}


class PlanoCreate(BaseModel):
    slug: str
    nome: str
    descricao: Optional[str] = None
    preco_mensal: Optional[float] = None
    preco_anual: Optional[float] = None
    moeda: str = "BRL"
    max_usuarios: Optional[int] = None
    max_propostas_mes: Optional[int] = None
    ai_credits_limit: int = 20
    permite_dominio_proprio: bool = False
    ordem: int = 0
    ativo: bool = True
    destaque: bool = False


class PlanoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco_mensal: Optional[float] = None
    preco_anual: Optional[float] = None
    moeda: Optional[str] = None
    max_usuarios: Optional[int] = None
    max_propostas_mes: Optional[int] = None
    ai_credits_limit: Optional[int] = None
    permite_dominio_proprio: Optional[bool] = None
    ordem: Optional[int] = None
    ativo: Optional[bool] = None
    destaque: Optional[bool] = None


class SolicitacaoPlano(BaseModel):
    slug: str
