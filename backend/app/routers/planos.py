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
async def solicitar_plano(
    data: SolicitacaoPlano,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    plano = await db.get(Plano, data.slug)
    if not plano or not plano.ativo:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    if plano.slug == empresa.plano:
        raise HTTPException(status_code=400, detail="Sua empresa já está neste plano")

    if plano.preco_mensal and plano.preco_mensal > 0:
        empresa.plano_solicitado = data.slug
        empresa.status_pagamento = "pendente"
        log = LogAdmin(
            empresa_id=empresa.id,
            superadmin_id=current_user.id,
            acao="solicitacao_plano",
            detalhes={"plano": data.slug, "status": "pendente"},
        )
        db.add(log)
        await db.commit()
        return {
            "message": "Solicitação de upgrade enviada. Um administrador irá aprovar.",
            "plano_solicitado": data.slug,
        }
    else:
        empresa.plano = data.slug
        empresa.plano_solicitado = None
        empresa.status_pagamento = "em_dia"
        await db.commit()
        return {"message": "Plano atualizado com sucesso", "plano": data.slug}


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
            "max_usuarios": plano.max_usuarios,
            "max_propostas_mes": plano.max_propostas_mes,
            "ai_credits_limit": plano.ai_credits_limit,
            "permite_dominio_proprio": plano.permite_dominio_proprio,
        }

    return {
        "plano": empresa.plano,
        "plano_solicitado": empresa.plano_solicitado,
        "status_pagamento": empresa.status_pagamento,
        "detalhes": plano_data,
    }
