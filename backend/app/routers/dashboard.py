from typing import Any, List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.proposta import Proposta, StatusProposta
from app.models.orcamento import Orcamento, StatusOrcamento
from app.models.usuario import Usuario
from app.core.dependencies import get_current_active_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

FUSO_BR = timezone(timedelta(hours=-3))


def get_period_date_filter(periodo: str):
    now = datetime.now(timezone.utc)
    if periodo == "hoje":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == "7dias":
        return now - timedelta(days=7)
    elif periodo == "30dias":
        return now - timedelta(days=30)
    elif periodo == "mes_atual":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif periodo == "ano_atual":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


@router.get("/metrics")
async def get_dashboard_metrics(
    periodo: str = Query("tudo", description="tudo, hoje, 7dias, 30dias, mes_atual, ano_atual"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
) -> Any:
    dt_inicio = get_period_date_filter(periodo)

    # 1. Total Propostas
    stmt_prop = select(func.count()).select_from(Proposta).where(
        Proposta.empresa_id == current_user.empresa_id
    )
    if dt_inicio:
        stmt_prop = stmt_prop.where(Proposta.created_at >= dt_inicio)
    total_propostas = await db.scalar(stmt_prop) or 0

    # 2. Total Orçamentos
    stmt_orc = select(func.count()).select_from(Orcamento).where(
        Orcamento.empresa_id == current_user.empresa_id
    )
    if dt_inicio:
        stmt_orc = stmt_orc.where(Orcamento.created_at >= dt_inicio)
    total_orcamentos = await db.scalar(stmt_orc) or 0

    # 3. Total Visualizações (Propostas + Orçamentos)
    stmt_views_p = select(func.sum(Proposta.visualizacoes)).where(
        Proposta.empresa_id == current_user.empresa_id
    )
    if dt_inicio:
        stmt_views_p = stmt_views_p.where(Proposta.created_at >= dt_inicio)
    views_prop = await db.scalar(stmt_views_p) or 0

    stmt_views_o = select(func.sum(Orcamento.visualizacoes)).where(
        Orcamento.empresa_id == current_user.empresa_id
    )
    if dt_inicio:
        stmt_views_o = stmt_views_o.where(Orcamento.created_at >= dt_inicio)
    views_orc = await db.scalar(stmt_views_o) or 0

    total_visualizacoes = views_prop + views_orc

    # 4. Pagamentos Pendentes / Em Análise (Propostas enviadas / em análise + Orçamentos enviados)
    stmt_pend_p = select(
        func.count(Proposta.id),
        func.sum(Proposta.valor_total)
    ).where(
        Proposta.empresa_id == current_user.empresa_id,
        Proposta.status.in_([StatusProposta.ENVIADA, StatusProposta.EM_ANALISE])
    )
    if dt_inicio:
        stmt_pend_p = stmt_pend_p.where(Proposta.created_at >= dt_inicio)
    res_pend_p = (await db.execute(stmt_pend_p)).first()
    pend_count_p = res_pend_p[0] or 0
    pend_val_p = float(res_pend_p[1] or 0.0)

    stmt_pend_o = select(
        func.count(Orcamento.id),
        func.sum(Orcamento.valor_total)
    ).where(
        Orcamento.empresa_id == current_user.empresa_id,
        Orcamento.status == StatusOrcamento.ENVIADO
    )
    if dt_inicio:
        stmt_pend_o = stmt_pend_o.where(Orcamento.created_at >= dt_inicio)
    res_pend_o = (await db.execute(stmt_pend_o)).first()
    pend_count_o = res_pend_o[0] or 0
    pend_val_o = float(res_pend_o[1] or 0.0)

    pagamentos_pendentes = pend_count_p + pend_count_o
    pagamentos_pendentes_valor = pend_val_p + pend_val_o

    # 5. Solicitações de Retorno (Propostas em análise ou com interação)
    solicitacoes_retorno = pend_count_p

    # 6. Vendas Fechadas (Propostas Aceitas + Orçamentos Aprovados)
    stmt_fech_p = select(
        func.count(Proposta.id),
        func.sum(Proposta.valor_total)
    ).where(
        Proposta.empresa_id == current_user.empresa_id,
        Proposta.status == StatusProposta.ACEITA
    )
    if dt_inicio:
        stmt_fech_p = stmt_fech_p.where(Proposta.created_at >= dt_inicio)
    res_fech_p = (await db.execute(stmt_fech_p)).first()
    fech_count_p = res_fech_p[0] or 0
    fech_val_p = float(res_fech_p[1] or 0.0)

    stmt_fech_o = select(
        func.count(Orcamento.id),
        func.sum(Orcamento.valor_total)
    ).where(
        Orcamento.empresa_id == current_user.empresa_id,
        Orcamento.status == StatusOrcamento.APROVADO
    )
    if dt_inicio:
        stmt_fech_o = stmt_fech_o.where(Orcamento.created_at >= dt_inicio)
    res_fech_o = (await db.execute(stmt_fech_o)).first()
    fech_count_o = res_fech_o[0] or 0
    fech_val_o = float(res_fech_o[1] or 0.0)

    vendas_fechadas = fech_count_p + fech_count_o
    receita_total = fech_val_p + fech_val_o

    # 7. Métricas Calculadas
    total_documentos = total_propostas + total_orcamentos
    taxa_conversao = (vendas_fechadas / total_documentos * 100) if total_documentos > 0 else 0.0
    ticket_medio = (receita_total / vendas_fechadas) if vendas_fechadas > 0 else 0.0

    return {
        "total_propostas": total_propostas,
        "total_orcamentos": total_orcamentos,
        "total_documentos": total_documentos,
        "total_visualizacoes": total_visualizacoes,
        "pagamentos_pendentes": pagamentos_pendentes,
        "pagamentos_pendentes_valor": pagamentos_pendentes_valor,
        "solicitacoes_retorno": solicitacoes_retorno,
        "vendas_fechadas": vendas_fechadas,
        "receita_total": receita_total,
        "taxa_conversao": round(taxa_conversao, 1),
        "ticket_medio": round(ticket_medio, 2),
    }


@router.get("/activities")
async def get_dashboard_activities(
    only_me: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
) -> Any:
    """Retorna o histórico recente de atividades e alterações de propostas e orçamentos."""
    # 1. Buscar propostas recentes
    stmt_p = select(Proposta).where(
        Proposta.empresa_id == current_user.empresa_id
    ).options(
        selectinload(Proposta.cliente),
        selectinload(Proposta.usuario)
    ).order_by(Proposta.updated_at.desc()).limit(limit)

    if only_me:
        stmt_p = stmt_p.where(Proposta.usuario_id == current_user.id)

    propostas = (await db.execute(stmt_p)).scalars().all()

    # 2. Buscar orçamentos recentes
    stmt_o = select(Orcamento).where(
        Orcamento.empresa_id == current_user.empresa_id
    ).options(
        selectinload(Orcamento.cliente),
        selectinload(Orcamento.usuario)
    ).order_by(Orcamento.updated_at.desc()).limit(limit)

    if only_me:
        stmt_o = stmt_o.where(Orcamento.usuario_id == current_user.id)

    orcamentos = (await db.execute(stmt_o)).scalars().all()

    # 3. Unir e normalizar
    items = []
    for p in propostas:
        items.append({
            "id": str(p.id),
            "tipo": "proposta",
            "numero": p.numero,
            "titulo": p.titulo,
            "cliente_nome": p.cliente.razao_social if p.cliente else "Cliente",
            "usuario_nome": p.usuario.nome if p.usuario else "Usuário",
            "usuario_id": str(p.usuario_id) if p.usuario_id else None,
            "status": p.status.value if hasattr(p.status, "value") else str(p.status),
            "valor_total": float(p.valor_total or 0.0),
            "visualizacoes": p.visualizacoes or 0,
            "data": (p.updated_at or p.created_at).isoformat() if (p.updated_at or p.created_at) else None,
            "link": f"/propostas/{p.id}/edit",
        })

    for o in orcamentos:
        items.append({
            "id": str(o.id),
            "tipo": "orcamento",
            "numero": o.numero,
            "titulo": o.titulo,
            "cliente_nome": o.cliente.razao_social if o.cliente else "Cliente",
            "usuario_nome": o.usuario.nome if o.usuario else "Usuário",
            "usuario_id": str(o.usuario_id) if o.usuario_id else None,
            "status": o.status.value if hasattr(o.status, "value") else str(o.status),
            "valor_total": float(o.valor_total or 0.0),
            "visualizacoes": o.visualizacoes or 0,
            "data": (o.updated_at or o.created_at).isoformat() if (o.updated_at or o.created_at) else None,
            "link": f"/orcamentos/{o.id}/edit",
        })

    # Ordenar pelo mais recente
    items.sort(key=lambda x: x["data"] or "", reverse=True)
    return items[:limit]
