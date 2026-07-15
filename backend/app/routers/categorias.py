from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate, CategoriaResponse, CategoriaListResponse
from app.core.dependencies import get_current_active_user
from app.models.usuario import Usuario

router = APIRouter(prefix="/api/categorias", tags=["categorias"])


@router.get("", response_model=CategoriaListResponse)
async def list_categorias(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    stmt = select(Categoria).where(Categoria.empresa_id == current_user.empresa_id)
    count_stmt = select(func.count()).select_from(Categoria).where(
        Categoria.empresa_id == current_user.empresa_id
    )

    if search:
        search_filter = Categoria.nome.ilike(f"%{search}%")
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total = await db.scalar(count_stmt)
    
    stmt = stmt.order_by(Categoria.nome.asc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
async def create_categoria(
    *,
    db: AsyncSession = Depends(get_db),
    categoria_in: CategoriaCreate,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    categoria = Categoria(
        **categoria_in.model_dump(),
        empresa_id=current_user.empresa_id,
    )
    db.add(categoria)
    await db.commit()
    await db.refresh(categoria)
    return categoria


@router.put("/{id}", response_model=CategoriaResponse)
async def update_categoria(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    categoria_in: CategoriaUpdate,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    categoria = await db.get(Categoria, id)
    if not categoria or categoria.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    update_data = categoria_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(categoria, field, value)

    await db.commit()
    await db.refresh(categoria)
    return categoria


@router.delete("/{id}")
async def delete_categoria(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    categoria = await db.get(Categoria, id)
    if not categoria or categoria.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    # TODO: Verify if there are any servicos using this categoria
    await db.delete(categoria)
    await db.commit()
    return {"ok": True}
