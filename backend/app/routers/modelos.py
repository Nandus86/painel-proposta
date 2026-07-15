from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.database import get_db
from app.models.modelo_proposta import ModeloProposta
from app.models.usuario import Usuario
from app.schemas.modelo_proposta import ModeloPropostaCreate, ModeloPropostaUpdate, ModeloPropostaResponse
from app.core.dependencies import get_current_active_user, require_admin

router = APIRouter(prefix="/api/modelos", tags=["Modelos de Proposta"])


@router.get("", response_model=List[ModeloPropostaResponse])
async def list_modelos(
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista todos os modelos de proposta da empresa do usuário."""
    result = await db.execute(
        select(ModeloProposta)
        .where(ModeloProposta.empresa_id == current_user.empresa_id)
        .order_by(ModeloProposta.titulo)
    )
    return result.scalars().all()


@router.get("/{modelo_id}", response_model=ModeloPropostaResponse)
async def get_modelo(
    modelo_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Busca os detalhes de um modelo de proposta específico."""
    result = await db.execute(
        select(ModeloProposta)
        .where(ModeloProposta.id == modelo_id, ModeloProposta.empresa_id == current_user.empresa_id)
    )
    modelo = result.scalar_one_or_none()
    if not modelo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modelo não encontrado")
    return modelo


@router.post("", response_model=ModeloPropostaResponse, status_code=status.HTTP_201_CREATED)
async def create_modelo(
    data: ModeloPropostaCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Cria um novo modelo de proposta."""
    modelo = ModeloProposta(
        empresa_id=current_user.empresa_id,
        **data.model_dump()
    )
    db.add(modelo)
    await db.commit()
    await db.refresh(modelo)
    return modelo


@router.put("/{modelo_id}", response_model=ModeloPropostaResponse)
async def update_modelo(
    modelo_id: uuid.UUID,
    data: ModeloPropostaUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza um modelo de proposta existente."""
    result = await db.execute(
        select(ModeloProposta)
        .where(ModeloProposta.id == modelo_id, ModeloProposta.empresa_id == current_user.empresa_id)
    )
    modelo = result.scalar_one_or_none()
    if not modelo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modelo não encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(modelo, key, value)

    await db.commit()
    await db.refresh(modelo)
    return modelo


@router.delete("/{modelo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_modelo(
    modelo_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Exclui um modelo de proposta."""
    result = await db.execute(
        select(ModeloProposta)
        .where(ModeloProposta.id == modelo_id, ModeloProposta.empresa_id == current_user.empresa_id)
    )
    modelo = result.scalar_one_or_none()
    if not modelo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modelo não encontrado")

    await db.delete(modelo)
    await db.commit()
    return None
