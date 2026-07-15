from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.database import get_db
from app.models.proposta import Proposta, StatusProposta
from app.models.empresa import Empresa

router = APIRouter(prefix="/api/public/propostas", tags=["Public"])

@router.get("/{token}")
async def get_public_proposta(token: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Busca uma proposta pelo token público para visualização do cliente."""
    result = await db.execute(
        select(Proposta)
        .options(selectinload(Proposta.items), selectinload(Proposta.empresa), selectinload(Proposta.cliente))
        .where(Proposta.token_publico == token)
    )
    proposta = result.scalar_one_or_none()

    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada ou link inválido.")

    # Increment view count
    proposta.visualizacoes += 1
    await db.commit()

    # Retorna dados limpos sem expor informações sensíveis do backend (como IDs internos)
    return {
        "titulo": proposta.titulo,
        "numero": proposta.numero,
        "status": proposta.status,
        "data_emissao": proposta.data_emissao,
        "data_validade": proposta.data_validade,
        "validade_dias": proposta.validade_dias,
        "valor_total": proposta.valor_total,
        "observacoes": proposta.observacoes,
        "condicoes_pagamento": proposta.condicoes_pagamento,
        "assinatura_data": proposta.assinatura_data,
        "empresa": {
            "razao_social": proposta.empresa.razao_social,
            "nome_fantasia": proposta.empresa.nome_fantasia,
            "cnpj": proposta.empresa.cnpj,
            "logo_url": proposta.empresa.logo_url,
            "email": proposta.empresa.email,
            "telefone": proposta.empresa.telefone
        },
        "cliente": {
            "razao_social": proposta.cliente.razao_social,
            "cnpj_cpf": proposta.cliente.cnpj or proposta.cliente.cpf
        },
        "items": [
            {
                "descricao": item.descricao,
                "quantidade": item.quantidade,
                "preco_unitario": item.preco_unitario,
                "subtotal": item.subtotal
            } for item in proposta.items
        ]
    }

class AceitarPropostaRequest(BaseModel):
    aceite: bool

@router.post("/{token}/aceitar")
async def aceitar_proposta(
    token: uuid.UUID,
    request: Request,
    body: AceitarPropostaRequest,
    db: AsyncSession = Depends(get_db)
):
    """Registra o aceite (assinatura digital) do cliente na proposta."""
    if not body.aceite:
        raise HTTPException(status_code=400, detail="É necessário confirmar o aceite.")

    result = await db.execute(
        select(Proposta).where(Proposta.token_publico == token)
    )
    proposta = result.scalar_one_or_none()

    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada.")

    if proposta.status == StatusProposta.ACEITA:
        raise HTTPException(status_code=400, detail="Esta proposta já foi aceita anteriormente.")

    # Coleta de dados para a assinatura simples
    client_host = request.client.host if request.client else "unknown"
    # Se estiver atrás de proxy (Nginx), pega o IP real
    real_ip = request.headers.get("X-Forwarded-For", client_host).split(",")[0].strip()

    from datetime import timezone
    proposta.status = StatusProposta.ACEITA
    proposta.assinatura_ip = real_ip
    proposta.assinatura_data = datetime.now(timezone.utc)

    await db.commit()

    return {"message": "Proposta aceita com sucesso!", "assinatura_data": proposta.assinatura_data}

# --- Rotas Públicas para Orçamentos ---

from app.models.orcamento import Orcamento, StatusOrcamento

orcamento_router = APIRouter(prefix="/api/public/orcamentos", tags=["Public"])

@orcamento_router.get("/{token}")
async def get_public_orcamento(token: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Busca um orçamento pelo token público para visualização do cliente."""
    result = await db.execute(
        select(Orcamento)
        .options(selectinload(Orcamento.items), selectinload(Orcamento.empresa), selectinload(Orcamento.cliente))
        .where(Orcamento.token_publico == token)
    )
    orcamento = result.scalar_one_or_none()

    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado ou link inválido.")

    # Increment view count
    orcamento.visualizacoes += 1
    await db.commit()

    return {
        "titulo": orcamento.titulo,
        "numero": orcamento.numero,
        "status": orcamento.status,
        "data_emissao": orcamento.data_emissao,
        "data_validade": orcamento.data_validade,
        "validade_dias": orcamento.validade_dias,
        "valor_total": orcamento.valor_total,
        "observacoes": orcamento.observacoes,
        "condicoes_pagamento": orcamento.condicoes_pagamento,
        "assinatura_data": orcamento.assinatura_data,
        "empresa": {
            "razao_social": orcamento.empresa.razao_social,
            "nome_fantasia": orcamento.empresa.nome_fantasia,
            "cnpj": orcamento.empresa.cnpj,
            "logo_url": orcamento.empresa.logo_url,
            "email": orcamento.empresa.email,
            "telefone": orcamento.empresa.telefone
        },
        "cliente": {
            "razao_social": orcamento.cliente.razao_social,
            "cnpj_cpf": orcamento.cliente.cnpj or orcamento.cliente.cpf
        },
        "items": [
            {
                "descricao": item.descricao,
                "quantidade": item.quantidade,
                "preco_unitario": item.preco_unitario,
                "subtotal": item.subtotal
            } for item in orcamento.items
        ]
    }

class AprovarOrcamentoRequest(BaseModel):
    aceite: bool

@orcamento_router.post("/{token}/aprovar")
async def aprovar_orcamento(
    token: uuid.UUID,
    request: Request,
    body: AprovarOrcamentoRequest,
    db: AsyncSession = Depends(get_db)
):
    """Registra a aprovação do cliente no orçamento."""
    if not body.aceite:
        raise HTTPException(status_code=400, detail="É necessário confirmar a aprovação.")

    result = await db.execute(
        select(Orcamento).where(Orcamento.token_publico == token)
    )
    orcamento = result.scalar_one_or_none()

    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")

    if orcamento.status == StatusOrcamento.APROVADO:
        raise HTTPException(status_code=400, detail="Este orçamento já foi aprovado anteriormente.")

    client_host = request.client.host if request.client else "unknown"
    real_ip = request.headers.get("X-Forwarded-For", client_host).split(",")[0].strip()

    from datetime import timezone
    orcamento.status = StatusOrcamento.APROVADO
    orcamento.assinatura_ip = real_ip
    orcamento.assinatura_data = datetime.now(timezone.utc)

    await db.commit()
    
    return {"message": "Orçamento aprovado com sucesso!", "assinatura_data": orcamento.assinatura_data}
