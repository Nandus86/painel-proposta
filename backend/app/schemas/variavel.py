from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid


class VariavelCatalogo(BaseModel):
    tag: str
    nome: str
    descricao: str
    categoria: str
    cor: str


class VariavelCustomizadaCreate(BaseModel):
    tag: str
    nome: str
    valor_padrao: Optional[str] = None


class VariavelCustomizadaUpdate(BaseModel):
    tag: Optional[str] = None
    nome: Optional[str] = None
    valor_padrao: Optional[str] = None


class VariavelCustomizadaResponse(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    tag: str
    nome: str
    valor_padrao: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


VARIABLE_CATALOG: list[VariavelCatalogo] = [
    VariavelCatalogo(tag="{{cliente}}", nome="Razão Social do Cliente", descricao="Nome oficial/razão social do cliente", categoria="cliente", cor="#3b82f6"),
    VariavelCatalogo(tag="{{cliente_fantasia}}", nome="Nome Fantasia do Cliente", descricao="Nome fantasia do cliente", categoria="cliente", cor="#3b82f6"),
    VariavelCatalogo(tag="{{cliente_cnpj}}", nome="CNPJ do Cliente", descricao="CNPJ do cliente", categoria="cliente", cor="#3b82f6"),
    VariavelCatalogo(tag="{{cliente_email}}", nome="Email do Cliente", descricao="Email do cliente", categoria="cliente", cor="#3b82f6"),
    VariavelCatalogo(tag="{{cliente_telefone}}", nome="Telefone do Cliente", descricao="Telefone do cliente", categoria="cliente", cor="#3b82f6"),
    VariavelCatalogo(tag="{{cliente_contato}}", nome="Nome do Contato", descricao="Nome da pessoa de contato no cliente", categoria="cliente", cor="#3b82f6"),
    VariavelCatalogo(tag="{{cliente_endereco}}", nome="Endereço do Cliente", descricao="Endereço completo do cliente", categoria="cliente", cor="#3b82f6"),
    VariavelCatalogo(tag="{{empresa}}", nome="Nome da Empresa", descricao="Nome fantasia da sua empresa", categoria="empresa", cor="#f39c12"),
    VariavelCatalogo(tag="{{empresa_cnpj}}", nome="CNPJ da Empresa", descricao="CNPJ da sua empresa", categoria="empresa", cor="#f39c12"),
    VariavelCatalogo(tag="{{empresa_email}}", nome="Email da Empresa", descricao="Email de contato da sua empresa", categoria="empresa", cor="#f39c12"),
    VariavelCatalogo(tag="{{empresa_telefone}}", nome="Telefone da Empresa", descricao="Telefone da sua empresa", categoria="empresa", cor="#f39c12"),
    VariavelCatalogo(tag="{{empresa_endereco}}", nome="Endereço da Empresa", descricao="Endereço completo da sua empresa", categoria="empresa", cor="#f39c12"),
    VariavelCatalogo(tag="{{empresa_responsavel}}", nome="Responsável Técnico", descricao="Nome do responsável técnico/comercial", categoria="empresa", cor="#f39c12"),
    VariavelCatalogo(tag="{{proposta_titulo}}", nome="Título da Proposta", descricao="Título da proposta comercial", categoria="proposta", cor="#16a34a"),
    VariavelCatalogo(tag="{{proposta_numero}}", nome="Número da Proposta", descricao="Número sequencial da proposta", categoria="proposta", cor="#16a34a"),
    VariavelCatalogo(tag="{{valor_total}}", nome="Valor Total", descricao="Valor total da proposta (R$)", categoria="proposta", cor="#16a34a"),
    VariavelCatalogo(tag="{{valor_total_extenso}}", nome="Valor por Extenso", descricao="Valor total por extenso", categoria="proposta", cor="#16a34a"),
    VariavelCatalogo(tag="{{condicoes_pagamento}}", nome="Condições de Pagamento", descricao="Condições de pagamento definidas", categoria="proposta", cor="#16a34a"),
    VariavelCatalogo(tag="{{itens}}", nome="Lista de Itens", descricao="Listagem descritiva dos itens/serviços", categoria="itens", cor="#8b5cf6"),
    VariavelCatalogo(tag="{{itens_tabela}}", nome="Tabela de Itens", descricao="Tabela formatada com itens, qtd e valores", categoria="itens", cor="#8b5cf6"),
    VariavelCatalogo(tag="{{vendedor_nome}}", nome="Nome do Vendedor", descricao="Nome do vendedor responsável", categoria="vendedor", cor="#ec4899"),
    VariavelCatalogo(tag="{{vendedor_email}}", nome="Email do Vendedor", descricao="Email do vendedor", categoria="vendedor", cor="#ec4899"),
    VariavelCatalogo(tag="{{vendedor_telefone}}", nome="Telefone do Vendedor", descricao="Telefone do vendedor", categoria="vendedor", cor="#ec4899"),
    VariavelCatalogo(tag="{{data_emissao}}", nome="Data de Emissão", descricao="Data de emissão da proposta", categoria="datas", cor="#06b6d4"),
    VariavelCatalogo(tag="{{data_validade}}", nome="Data de Validade", descricao="Data de validade da proposta", categoria="datas", cor="#06b6d4"),
    VariavelCatalogo(tag="{{validade_dias}}", nome="Dias de Validade", descricao="Quantidade de dias de validade", categoria="datas", cor="#06b6d4"),
]
