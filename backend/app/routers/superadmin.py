from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, text, case, cast, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.proposta import Proposta
from app.models.orcamento import Orcamento
from app.models.log_admin import LogAdmin
from app.core.dependencies import require_superuser

router = APIRouter(prefix="/api/superadmin", tags=["Super Admin"])


@router.get("/dashboard")
async def superadmin_dashboard(
    current_user: Usuario = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    total_empresas = await db.scalar(select(func.count(Empresa.id)))
    total_empresas_ativas = await db.scalar(
        select(func.count(Empresa.id)).where(Empresa.ativo == True)
    )
    total_usuarios = await db.scalar(select(func.count(Usuario.id)))

    total_propostas = await db.scalar(select(func.count(Proposta.id)))
    total_orcamentos = await db.scalar(select(func.count(Orcamento.id)))

    hoje = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)
    trinta_dias_atras = hoje - timedelta(days=30)

    novas_empresas_30d = await db.scalar(
        select(func.count(Empresa.id)).where(Empresa.created_at >= trinta_dias_atras)
    )

    propostas_hoje = await db.scalar(
        select(func.count(Proposta.id)).where(Proposta.data_emissao >= hoje)
    )
    propostas_mes = await db.scalar(
        select(func.count(Proposta.id)).where(Proposta.data_emissao >= inicio_mes)
    )

    orcamentos_hoje = await db.scalar(
        select(func.count(Orcamento.id)).where(Orcamento.data_emissao >= hoje)
    )
    orcamentos_mes = await db.scalar(
        select(func.count(Orcamento.id)).where(Orcamento.data_emissao >= inicio_mes)
    )

    total_creditos_ai_consumidos = await db.scalar(
        select(func.sum(Empresa.ai_credits_used_today))
    ) or 0

    empresas_por_plano = await db.execute(
        select(Empresa.plano, func.count(Empresa.id).label("total"))
        .group_by(Empresa.plano)
    )
    plano_rows = empresas_por_plano.all()

    empresas_por_pagamento = await db.execute(
        select(Empresa.status_pagamento, func.count(Empresa.id).label("total"))
        .group_by(Empresa.status_pagamento)
    )
    pagamento_rows = empresas_por_pagamento.all()

    ultimas_empresas = await db.execute(
        select(Empresa).order_by(Empresa.created_at.desc()).limit(10)
    )
    ultimas = ultimas_empresas.scalars().all()

    return {
        "empresas": {
            "total": total_empresas,
            "ativas": total_empresas_ativas,
            "inativas": total_empresas - total_empresas_ativas,
            "novas_30d": novas_empresas_30d,
        },
        "usuarios": {
            "total": total_usuarios,
        },
        "propostas": {
            "total": total_propostas,
            "hoje": propostas_hoje,
            "mes": propostas_mes,
        },
        "orcamentos": {
            "total": total_orcamentos,
            "hoje": orcamentos_hoje,
            "mes": orcamentos_mes,
        },
        "ia": {
            "creditos_consumidos_total": total_creditos_ai_consumidos or 0,
        },
        "empresas_por_plano": [
            {"plano": row.plano or "gratuito", "total": row.total}
            for row in plano_rows
        ],
        "empresas_por_pagamento": [
            {"status": row.status_pagamento or "em_dia", "total": row.total}
            for row in pagamento_rows
        ],
        "ultimas_empresas": [
            {
                "id": str(e.id),
                "razao_social": e.razao_social,
                "plano": e.plano,
                "status_pagamento": e.status_pagamento,
                "ativo": e.ativo,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in ultimas
        ],
    }


@router.get("/empresas/{id}/detalhes")
async def superadmin_empresa_detalhes(
    id: UUID,
    current_user: Usuario = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Empresa).where(Empresa.id == id).options(
            selectinload(Empresa.usuarios),
            selectinload(Empresa.propostas),
        )
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    total_propostas = await db.scalar(
        select(func.count(Proposta.id)).where(Proposta.empresa_id == id)
    )
    total_orcamentos = await db.scalar(
        select(func.count(Orcamento.id)).where(Orcamento.empresa_id == id)
    )

    ultimas_propostas = await db.execute(
        select(Proposta).where(Proposta.empresa_id == id).order_by(Proposta.data_emissao.desc()).limit(5)
    )
    propostas_list = ultimas_propostas.scalars().all()

    logs = await db.execute(
        select(LogAdmin).where(LogAdmin.empresa_id == id).order_by(LogAdmin.created_at.desc()).limit(20)
    )
    logs_list = logs.scalars().all()

    return {
        "empresa": {
            "id": str(empresa.id),
            "razao_social": empresa.razao_social,
            "nome_fantasia": empresa.nome_fantasia,
            "cnpj": empresa.cnpj,
            "email": empresa.email,
            "telefone": empresa.telefone,
            "cidade": empresa.cidade,
            "estado": empresa.estado,
            "plano": empresa.plano,
            "status_pagamento": empresa.status_pagamento,
            "ativo": empresa.ativo,
            "subdominio": empresa.subdominio,
            "dominio_personalizado": empresa.dominio_personalizado,
            "ai_credits_used_today": empresa.ai_credits_used_today,
            "ai_credits_limit": empresa.ai_credits_limit,
            "created_at": empresa.created_at.isoformat() if empresa.created_at else None,
        },
        "estatisticas": {
            "total_propostas": total_propostas,
            "total_orcamentos": total_orcamentos,
            "total_usuarios": len(empresa.usuarios) if empresa.usuarios else 0,
        },
        "usuarios": [
            {
                "id": str(u.id),
                "nome": u.nome,
                "email": u.email,
                "role": u.role.value,
                "cargo": u.cargo,
                "ativo": u.ativo,
                "is_superuser": u.is_superuser,
            }
            for u in (empresa.usuarios or [])
        ],
        "ultimas_propostas": [
            {
                "id": str(p.id),
                "numero": p.numero,
                "titulo": p.titulo,
                "status": p.status.value if p.status else None,
                "valor_total": float(p.valor_total) if p.valor_total else 0,
                "data_emissao": p.data_emissao.isoformat() if p.data_emissao else None,
            }
            for p in propostas_list
        ],
        "logs": [
            {
                "id": str(l.id),
                "acao": l.acao,
                "detalhes": l.detalhes,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs_list
        ],
    }


@router.post("/empresas/{id}/acao")
async def superadmin_empresa_acao(
    id: UUID,
    acao: str = "bloquear",
    motivo: str = "",
    current_user: Usuario = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Empresa).where(Empresa.id == id)
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    if acao == "bloquear":
        empresa.ativo = False
        detalhes = {"acao": "bloquear", "motivo": motivo}
    elif acao == "desbloquear":
        empresa.ativo = True
        detalhes = {"acao": "desbloquear", "motivo": motivo}
    elif acao == "resetar_senha_admin":
        admin = await db.execute(
            select(Usuario).where(
                Usuario.empresa_id == id,
                Usuario.role == "admin"
            ).limit(1)
        )
        admin_user = admin.scalar_one_or_none()
        if admin_user:
            from app.core.security import get_password_hash
            nova_senha = f"Reset{str(uuid.uuid4())[:8]}!"
            admin_user.senha_hash = get_password_hash(nova_senha)
            detalhes = {"acao": "resetar_senha_admin", "email": admin_user.email, "nova_senha": nova_senha}
        else:
            raise HTTPException(status_code=404, detail="Nenhum admin encontrado para esta empresa")
    elif acao == "limpar_dados":
        detalhes = {"acao": "limpar_dados", "status": "não implementado (marcação apenas)"}
    else:
        raise HTTPException(status_code=400, detail="Ação inválida")

    log = LogAdmin(
        empresa_id=id,
        superadmin_id=current_user.id,
        acao=acao,
        detalhes=detalhes,
    )
    db.add(log)
    await db.flush()
    await db.refresh(empresa)

    result_data = {"ok": True, "acao": acao, "detalhes": detalhes}
    if acao == "resetar_senha_admin":
        result_data["nova_senha"] = detalhes.get("nova_senha")

    return result_data


@router.get("/empresas/{id}/logs")
async def superadmin_empresa_logs(
    id: UUID,
    limit: int = 50,
    current_user: Usuario = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    logs = await db.execute(
        select(LogAdmin)
        .where(LogAdmin.empresa_id == id)
        .order_by(LogAdmin.created_at.desc())
        .limit(limit)
    )
    logs_list = logs.scalars().all()

    return {
        "empresa_id": str(id),
        "total": len(logs_list),
        "logs": [
            {
                "id": str(l.id),
                "acao": l.acao,
                "detalhes": l.detalhes,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs_list
        ],
    }
