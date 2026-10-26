"""Rotas públicas (sem login) usadas pelo cliente final para ver e aceitar documentos."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.orcamento import Orcamento, StatusOrcamento
from app.models.proposta import Proposta, StatusProposta
from app.schemas.empresa import documento_publico
from app.services import email as email_service
from app.services.notificacoes import descrever_documento, notificar
from app.services.pdf import format_brl
from app.config import settings

router = APIRouter(prefix="/api/public/propostas", tags=["Public"])
orcamento_router = APIRouter(prefix="/api/public/orcamentos", tags=["Public"])


class AceiteRequest(BaseModel):
    aceite: bool


def _client_ip(request: Request) -> str:
    # O uvicorn roda com --proxy-headers: request.client já é o IP real repassado pelo nginx
    return (request.client.host if request.client else "desconhecido")[:45]


def _expirado(doc) -> bool:
    val = doc.data_validade
    if not val:
        return False
    if val.tzinfo is None:
        val = val.replace(tzinfo=timezone.utc)
    return val < datetime.now(timezone.utc)


def _serialize(doc) -> dict:
    empresa, cliente = doc.empresa, doc.cliente
    return {
        "titulo": doc.titulo,
        "numero": doc.numero,
        "status": doc.status,
        "expirado": _expirado(doc),
        "data_emissao": doc.data_emissao,
        "data_validade": doc.data_validade,
        "validade_dias": doc.validade_dias,
        "valor_total": doc.valor_total,
        "observacoes": doc.observacoes,
        "condicoes_pagamento": doc.condicoes_pagamento,
        "assinatura_data": doc.assinatura_data,
        "empresa": {
            "razao_social": empresa.razao_social,
            "nome_fantasia": empresa.nome_fantasia,
            "cnpj": documento_publico(empresa.cnpj),
            "logo_url": empresa.logo_url,
            "email": empresa.email,
            "telefone": empresa.telefone,
            "cor_marca": empresa.cor_marca,
        },
        "cliente": {
            "razao_social": cliente.razao_social,
            "cnpj_cpf": cliente.cnpj or cliente.cpf,
        },
        "items": [
            {
                "descricao": item.descricao,
                "quantidade": item.quantidade,
                "preco_unitario": item.preco_unitario,
                "desconto": item.desconto,
                "subtotal": item.subtotal,
            }
            for item in sorted(doc.items, key=lambda i: i.ordem or 0)
        ],
    }


async def _load(db: AsyncSession, Model, token: uuid.UUID, nao_encontrado: str):
    result = await db.execute(
        select(Model)
        .options(
            selectinload(Model.items),
            selectinload(Model.empresa),
            selectinload(Model.cliente),
            selectinload(Model.usuario),
        )
        .where(Model.token_publico == token)
    )
    doc = result.scalar_one_or_none()
    if not doc or not doc.empresa.ativo:
        raise HTTPException(status_code=404, detail=nao_encontrado)
    return doc


async def _registrar_visualizacao(db: AsyncSession, Model, doc) -> None:
    # Lido antes do UPDATE: o SQLAlchemy sincroniza o objeto em memória após a atualização
    primeira_visualizacao = not doc.visualizacoes
    # Incremento atômico no banco (não perde contagem com acessos simultâneos)
    await db.execute(
        update(Model).where(Model.id == doc.id).values(visualizacoes=Model.visualizacoes + 1)
    )
    if primeira_visualizacao:
        rotulo, link = descrever_documento(doc)
        await notificar(
            db, empresa_id=doc.empresa_id, usuario_id=doc.usuario_id, tipo="visualizada",
            titulo=f"{doc.cliente.razao_social} abriu {rotulo.lower()}",
            mensagem=f"Primeira visualização pelo cliente: \"{doc.titulo}\".",
            link=link, referencia_id=doc.id, unica=True,
        )
    await db.commit()


async def _registrar_aceite(db: AsyncSession, doc, background: BackgroundTasks, verbo: str) -> None:
    """Notifica o vendedor no painel e por e-mail (em background) que o cliente aceitou."""
    rotulo, link = descrever_documento(doc)
    titulo = f"{rotulo} {verbo} por {doc.cliente.razao_social}"
    await notificar(
        db, empresa_id=doc.empresa_id, usuario_id=doc.usuario_id, tipo="aceita",
        titulo=titulo, mensagem=f"\"{doc.titulo}\" — {format_brl(doc.valor_total)}",
        link=link, referencia_id=doc.id,
    )
    if doc.usuario and doc.usuario.email:
        html = email_service.render_system_email(
            titulo,
            [
                f"Olá, {doc.usuario.nome}!",
                f"{doc.cliente.razao_social} acaba de dar o aceite em \"{doc.titulo}\", "
                f"no valor de {format_brl(doc.valor_total)}.",
                "O registro (data e IP) ficou salvo no documento.",
            ],
            "Abrir no painel",
            f"{settings.FRONTEND_URL.rstrip('/')}{link}",
            cor=doc.empresa.cor_marca or "#16a34a",
        )
        background.add_task(email_service.send_notification_email, doc.empresa, doc.usuario.email, titulo, html)


@router.get("/{token}")
async def get_public_proposta(token: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Busca uma proposta pelo token público para visualização do cliente."""
    proposta = await _load(db, Proposta, token, "Proposta não encontrada ou link inválido.")
    data = _serialize(proposta)
    await _registrar_visualizacao(db, Proposta, proposta)
    return data


@router.post("/{token}/aceitar")
async def aceitar_proposta(
    token: uuid.UUID,
    request: Request,
    body: AceiteRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Registra o aceite (assinatura eletrônica simples) do cliente na proposta."""
    if not body.aceite:
        raise HTTPException(status_code=400, detail="É necessário confirmar o aceite.")

    proposta = await _load(db, Proposta, token, "Proposta não encontrada.")
    if proposta.status == StatusProposta.ACEITA:
        raise HTTPException(status_code=400, detail="Esta proposta já foi aceita anteriormente.")
    if proposta.status in (StatusProposta.RECUSADA, StatusProposta.EXPIRADA):
        raise HTTPException(status_code=400, detail="Esta proposta não está mais disponível para aceite.")
    if _expirado(proposta):
        raise HTTPException(status_code=400, detail="Esta proposta expirou e não pode mais ser aceita.")

    proposta.status = StatusProposta.ACEITA
    proposta.assinatura_ip = _client_ip(request)
    proposta.assinatura_data = datetime.now(timezone.utc)
    await _registrar_aceite(db, proposta, background, "aceita")
    await db.commit()

    return {"message": "Proposta aceita com sucesso!", "assinatura_data": proposta.assinatura_data}


@orcamento_router.get("/{token}")
async def get_public_orcamento(token: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Busca um orçamento pelo token público para visualização do cliente."""
    orcamento = await _load(db, Orcamento, token, "Orçamento não encontrado ou link inválido.")
    data = _serialize(orcamento)
    await _registrar_visualizacao(db, Orcamento, orcamento)
    return data


@orcamento_router.post("/{token}/aprovar")
@orcamento_router.post("/{token}/aceitar")
async def aprovar_orcamento(
    token: uuid.UUID,
    request: Request,
    body: AceiteRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Registra a aprovação do cliente no orçamento."""
    if not body.aceite:
        raise HTTPException(status_code=400, detail="É necessário confirmar a aprovação.")

    orcamento = await _load(db, Orcamento, token, "Orçamento não encontrado.")
    if orcamento.status == StatusOrcamento.APROVADO:
        raise HTTPException(status_code=400, detail="Este orçamento já foi aprovado anteriormente.")
    if orcamento.status in (StatusOrcamento.REJEITADO, StatusOrcamento.VENCIDO):
        raise HTTPException(status_code=400, detail="Este orçamento não está mais disponível para aprovação.")
    if _expirado(orcamento):
        raise HTTPException(status_code=400, detail="Este orçamento expirou e não pode mais ser aprovado.")

    orcamento.status = StatusOrcamento.APROVADO
    orcamento.assinatura_ip = _client_ip(request)
    orcamento.assinatura_data = datetime.now(timezone.utc)
    await _registrar_aceite(db, orcamento, background, "aprovado")
    await db.commit()

    return {"message": "Orçamento aprovado com sucesso!", "assinatura_data": orcamento.assinatura_data}
