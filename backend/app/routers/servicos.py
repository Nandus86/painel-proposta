from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from uuid import UUID

from app.database import get_db
from app.models.servico import Servico
from app.schemas.servico import ServicoCreate, ServicoUpdate, ServicoResponse, ServicoListResponse
from app.core.dependencies import get_current_active_user
from app.models.usuario import Usuario

router = APIRouter(prefix="/api/servicos", tags=["servicos"])


@router.get("", response_model=ServicoListResponse)
async def list_servicos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    categoria_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    stmt = select(Servico).options(joinedload(Servico.categoria)).where(Servico.empresa_id == current_user.empresa_id)
    count_stmt = select(func.count()).select_from(Servico).where(
        Servico.empresa_id == current_user.empresa_id
    )

    if search:
        search_filter = or_(
            Servico.nome.ilike(f"%{search}%"),
            Servico.descricao_padrao.ilike(f"%{search}%")
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)
        
    if categoria_id:
        stmt = stmt.where(Servico.categoria_id == categoria_id)
        count_stmt = count_stmt.where(Servico.categoria_id == categoria_id)

    total = await db.scalar(count_stmt)
    
    stmt = stmt.order_by(Servico.nome.asc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("", response_model=ServicoResponse, status_code=status.HTTP_201_CREATED)
async def create_servico(
    *,
    db: AsyncSession = Depends(get_db),
    servico_in: ServicoCreate,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    servico = Servico(
        **servico_in.model_dump(),
        empresa_id=current_user.empresa_id,
    )
    db.add(servico)
    await db.commit()
    await db.refresh(servico)
    # Reload with joined relationships
    result = await db.execute(
        select(Servico).options(joinedload(Servico.categoria)).where(Servico.id == servico.id)
    )
    return result.scalar_one()


@router.put("/{id}", response_model=ServicoResponse)
async def update_servico(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    servico_in: ServicoUpdate,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    result = await db.execute(select(Servico).options(joinedload(Servico.categoria)).where(Servico.id == id))
    servico = result.scalar_one_or_none()
    
    if not servico or servico.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    update_data = servico_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(servico, field, value)

    await db.commit()
    await db.refresh(servico)
    # Reload to get updated relationships
    result = await db.execute(
        select(Servico).options(joinedload(Servico.categoria)).where(Servico.id == servico.id)
    )
    return result.scalar_one()


@router.delete("/{id}")
async def delete_servico(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    servico = await db.get(Servico, id)
    if not servico or servico.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    await db.delete(servico)
    await db.commit()
    return {"ok": True}
