from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import re

from app.database import get_db
from app.models.modelo_proposta import ModeloProposta
from app.models.usuario import Usuario
from app.models.variavel_customizada import VariavelCustomizada
from app.schemas.modelo_proposta import ModeloPropostaCreate, ModeloPropostaUpdate, ModeloPropostaResponse
from app.schemas.variavel import (
    VariavelCatalogo, VariavelCustomizadaCreate, VariavelCustomizadaUpdate,
    VariavelCustomizadaResponse, VARIABLE_CATALOG
)
from app.core.dependencies import get_current_active_user, require_admin

router = APIRouter(prefix="/api/modelos", tags=["Modelos de Proposta"])


TAG_REGEX = re.compile(r"^\{\{[a-z][a-z0-9_]+\}\}$")


@router.get("/variaveis")
async def list_variaveis(
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(VariavelCustomizada)
        .where(VariavelCustomizada.empresa_id == current_user.empresa_id)
        .order_by(VariavelCustomizada.nome)
    )
    customizadas = result.scalars().all()

    return {
        "sistema": [
            {"tag": v.tag, "nome": v.nome, "descricao": v.descricao, "categoria": v.categoria, "cor": v.cor}
            for v in VARIABLE_CATALOG
        ],
        "customizadas": [
            {"id": str(c.id), "tag": c.tag, "nome": c.nome, "valor_padrao": c.valor_padrao, "cor": "#a855f7"}
            for c in customizadas
        ]
    }


@router.post("/variaveis/customizadas", response_model=VariavelCustomizadaResponse, status_code=status.HTTP_201_CREATED)
async def create_variavel_customizada(
    data: VariavelCustomizadaCreate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    if not TAG_REGEX.match(data.tag):
        raise HTTPException(status_code=400, detail="Tag deve estar no formato {{nome_variavel}} (letras minúsculas, números e underscore)")

    existing = await db.execute(
        select(VariavelCustomizada).where(
            VariavelCustomizada.empresa_id == current_user.empresa_id,
            VariavelCustomizada.tag == data.tag
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Já existe uma variável customizada com esta tag")

    count = await db.execute(
        select(VariavelCustomizada).where(VariavelCustomizada.empresa_id == current_user.empresa_id)
    )
    if len(count.scalars().all()) >= 50:
        raise HTTPException(status_code=400, detail="Limite de 50 variáveis customizadas atingido")

    variavel = VariavelCustomizada(
        empresa_id=current_user.empresa_id,
        tag=data.tag,
        nome=data.nome,
        valor_padrao=data.valor_padrao
    )
    db.add(variavel)
    await db.commit()
    await db.refresh(variavel)
    return variavel


@router.put("/variaveis/customizadas/{variavel_id}", response_model=VariavelCustomizadaResponse)
async def update_variavel_customizada(
    variavel_id: uuid.UUID,
    data: VariavelCustomizadaUpdate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(VariavelCustomizada).where(
            VariavelCustomizada.id == variavel_id,
            VariavelCustomizada.empresa_id == current_user.empresa_id
        )
    )
    variavel = result.scalar_one_or_none()
    if not variavel:
        raise HTTPException(status_code=404, detail="Variável customizada não encontrada")

    if data.tag is not None:
        if not TAG_REGEX.match(data.tag):
            raise HTTPException(status_code=400, detail="Tag deve estar no formato {{nome_variavel}}")
        existing = await db.execute(
            select(VariavelCustomizada).where(
                VariavelCustomizada.empresa_id == current_user.empresa_id,
                VariavelCustomizada.tag == data.tag,
                VariavelCustomizada.id != variavel_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Já existe uma variável com esta tag")
        variavel.tag = data.tag

    if data.nome is not None:
        variavel.nome = data.nome
    if data.valor_padrao is not None:
        variavel.valor_padrao = data.valor_padrao

    await db.commit()
    await db.refresh(variavel)
    return variavel


@router.delete("/variaveis/customizadas/{variavel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variavel_customizada(
    variavel_id: uuid.UUID,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(VariavelCustomizada).where(
            VariavelCustomizada.id == variavel_id,
            VariavelCustomizada.empresa_id == current_user.empresa_id
        )
    )
    variavel = result.scalar_one_or_none()
    if not variavel:
        raise HTTPException(status_code=404, detail="Variável customizada não encontrada")

    await db.delete(variavel)
    await db.commit()
    return None


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
