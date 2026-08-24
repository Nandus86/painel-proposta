from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.plano import Plano
from app.models.log_admin import LogAdmin
from app.schemas.plano import PlanoResponse, PlanoCreate, PlanoUpdate, SolicitacaoPlano
from app.core.dependencies import get_current_user, require_admin, require_superuser

router = APIRouter(prefix="/api/planos", tags=["Planos"])


@router.get("", response_model=list[PlanoResponse])
async def listar_planos(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Plano).where(Plano.ativo == True).order_by(Plano.ordem)
    )
    return result.scalars().all()


@router.get("/admin/todos", response_model=list[PlanoResponse])
async def listar_todos_planos(
    current_user: Usuario = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Plano).order_by(Plano.ordem))
    return result.scalars().all()


@router.post("/admin", response_model=PlanoResponse, status_code=status.HTTP_201_CREATED)
async def criar_plano(
    data: PlanoCreate,
    current_user: Usuario = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.get(Plano, data.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Slug já existe")
    plano = Plano(**data.model_dump())
    db.add(plano)
    await db.commit()
    await db.refresh(plano)
    return plano


@router.put("/admin/{slug}", response_model=PlanoResponse)
async def atualizar_plano(
    slug: str,
    data: PlanoUpdate,
    current_user: Usuario = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    plano = await db.get(Plano, slug)
    if not plano:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plano, field, value)
    await db.commit()
    await db.refresh(plano)
    return plano


@router.delete("/admin/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_plano(
    slug: str,
    current_user: Usuario = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    plano = await db.get(Plano, slug)
    if not plano:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    await db.delete(plano)
    await db.commit()


@router.post("/me/solicitar")
@router.post("/me/alterar")
async def solicitar_ou_alterar_plano(
    data: SolicitacaoPlano,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Altera o plano da empresa ativa imediatamente.
    Atualiza empresa.plano, limites de IA e status de pagamento.
    Preparado para integração posterior com Stripe ou Asaas.
    """
    plano = await db.get(Plano, data.slug)
    if not plano or not plano.ativo:
        raise HTTPException(status_code=404, detail="Plano não encontrado ou inativo")

    result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    plano_anterior = empresa.plano
    if plano.slug == plano_anterior:
        return {
            "message": f"Sua empresa já está no plano {plano.nome}",
            "plano": plano.slug,
            "detalhes": {
                "slug": plano.slug,
                "nome": plano.nome,
                "max_usuarios": plano.max_usuarios,
                "max_propostas_mes": plano.max_propostas_mes,
                "ai_credits_limit": plano.ai_credits_limit,
                "permite_dominio_proprio": plano.permite_dominio_proprio,
            }
        }

    # Atualiza o plano da empresa e sincroniza limites
    empresa.plano = plano.slug
    empresa.plano_solicitado = None
    empresa.status_pagamento = "em_dia"
    empresa.ai_credits_limit = plano.ai_credits_limit

    # Registrar log de auditoria
    log = LogAdmin(
        empresa_id=empresa.id,
        superadmin_id=current_user.id,
        acao="alteracao_plano",
        detalhes={
            "plano_anterior": plano_anterior,
            "plano_novo": plano.slug,
            "status": "em_dia"
        },
    )
    db.add(log)
    await db.commit()
    await db.refresh(empresa)

    return {
        "message": f"Plano alterado com sucesso para {plano.nome}!",
        "plano": plano.slug,
        "detalhes": {
            "slug": plano.slug,
            "nome": plano.nome,
            "max_usuarios": plano.max_usuarios,
            "max_propostas_mes": plano.max_propostas_mes,
            "ai_credits_limit": plano.ai_credits_limit,
            "permite_dominio_proprio": plano.permite_dominio_proprio,
        }
    }


@router.get("/me/atual")
async def plano_atual(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    plano = await db.get(Plano, empresa.plano)
    plano_data = None
    if plano:
        plano_data = {
            "slug": plano.slug,
            "nome": plano.nome,
            "descricao": plano.descricao,
            "preco_mensal": float(plano.preco_mensal) if plano.preco_mensal else None,
            "preco_anual": float(plano.preco_anual) if plano.preco_anual else None,
            "max_usuarios": plano.max_usuarios,
            "max_propostas_mes": plano.max_propostas_mes,
            "ai_credits_limit": plano.ai_credits_limit,
            "permite_dominio_proprio": plano.permite_dominio_proprio,
            "destaque": plano.destaque,
        }

    return {
        "plano": empresa.plano,
        "plano_solicitado": empresa.plano_solicitado,
        "status_pagamento": empresa.status_pagamento,
        "detalhes": plano_data,
    }
