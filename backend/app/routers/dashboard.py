from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.proposta import Proposta, StatusProposta
from app.models.usuario import Usuario
from app.core.dependencies import get_current_active_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/metrics")
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
) -> Any:
    # 1. Total propostas criadas
    stmt_total = select(func.count()).select_from(Proposta).where(
        Proposta.empresa_id == current_user.empresa_id
    )
    total_propostas = await db.scalar(stmt_total) or 0

    # 2. Total visualizações
    stmt_views = select(func.sum(Proposta.visualizacoes)).where(
        Proposta.empresa_id == current_user.empresa_id
    )
    total_visualizacoes = await db.scalar(stmt_views) or 0

    # 3. Vendas fechadas (Propostas Aceitas)
    stmt_fechadas = select(func.count()).select_from(Proposta).where(
        Proposta.empresa_id == current_user.empresa_id,
        Proposta.status == StatusProposta.ACEITA
    )
    vendas_fechadas = await db.scalar(stmt_fechadas) or 0

    # 4. Receita Total (Soma valor_total de propostas Aceitas)
    stmt_receita = select(func.sum(Proposta.valor_total)).where(
        Proposta.empresa_id == current_user.empresa_id,
        Proposta.status == StatusProposta.ACEITA
    )
    receita_total = await db.scalar(stmt_receita) or 0.0

    return {
        "total_propostas": total_propostas,
        "total_visualizacoes": total_visualizacoes,
        "vendas_fechadas": vendas_fechadas,
        "receita_total": float(receita_total)
    }
