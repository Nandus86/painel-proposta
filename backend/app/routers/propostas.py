from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timedelta, timezone

FUSO_BR = timezone(timedelta(hours=-3))

from app.database import get_db
from app.models.proposta import Proposta, ItemProposta, StatusProposta
from app.models.cliente import Cliente
from app.schemas.proposta import (
    PropostaCreate, 
    PropostaUpdate, 
    PropostaResponse, 
    PropostaList,
    ItemPropostaCreate
)
from app.core.dependencies import get_current_active_user
from app.models.usuario import Usuario

router = APIRouter(prefix="/api/propostas", tags=["propostas"])


@router.get("", response_model=dict[str, Any])
async def list_propostas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    status: StatusProposta | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    stmt = select(Proposta).where(Proposta.empresa_id == current_user.empresa_id)
    count_stmt = select(func.count()).select_from(Proposta).where(
        Proposta.empresa_id == current_user.empresa_id
    )

    if status:
        stmt = stmt.where(Proposta.status == status)
        count_stmt = count_stmt.where(Proposta.status == status)

    if search:
        search_filter = or_(
            Proposta.titulo.ilike(f"%{search}%"),
            # Proposta.cliente.razao_social.ilike(f"%{search}%") # Requires join
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total = await db.scalar(count_stmt)
    
    # Load cliente for the list
    stmt = stmt.options(selectinload(Proposta.cliente))
    stmt = stmt.order_by(Proposta.numero.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    propostas = result.scalars().all()

    # Map to PropostaList schema manually if needed, or rely on response_model
    items = []
    for p in propostas:
        items.append({
            "id": p.id,
            "numero": p.numero,
            "titulo": p.titulo,
            "cliente_nome": p.cliente.razao_social,
            "status": p.status,
            "valor_total": p.valor_total,
            "data_emissao": p.data_emissao,
            "data_validade": p.data_validade,
            "token_publico": p.token_publico
        })

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{id}", response_model=PropostaResponse)
async def get_proposta(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    stmt = select(Proposta).where(
        Proposta.id == id, 
        Proposta.empresa_id == current_user.empresa_id
    ).options(
        selectinload(Proposta.items),
        selectinload(Proposta.cliente)
    )
    result = await db.execute(stmt)
    proposta = result.scalar_one_or_none()
    
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    
    return proposta


@router.post("", response_model=PropostaResponse, status_code=status.HTTP_201_CREATED)
async def create_proposta(
    *,
    db: AsyncSession = Depends(get_db),
    proposta_in: PropostaCreate,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    # 1. Get next proposal number for the company
    result = await db.execute(
        select(func.max(Proposta.numero)).where(Proposta.empresa_id == current_user.empresa_id)
    )
    max_numero = result.scalar() or 0
    next_numero = max_numero + 1

    # 2. Create Proposta
    proposta_dict = proposta_in.model_dump(exclude={"items"})
    
    # Calculate total value from items
    total_value = sum(item.subtotal for item in proposta_in.items)
    
    # Set expiration date if not provided
    validade_dias = proposta_dict.get("validade_dias") or 15
    if not proposta_dict.get("data_validade"):
        proposta_dict["data_validade"] = datetime.now(FUSO_BR) + timedelta(days=validade_dias)

    proposta = Proposta(
        **proposta_dict,
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        numero=next_numero,
        valor_total=total_value,
        data_emissao=datetime.now(FUSO_BR)
    )
    
    db.add(proposta)
    await db.flush() 
    
    # 2. Create Items
    for item_in in proposta_in.items:
        item = ItemProposta(
            **item_in.model_dump(),
            proposta_id=proposta.id
        )
        db.add(item)
    
    await db.commit()
    
    # Refresh with items
    stmt = select(Proposta).where(Proposta.id == proposta.id).options(selectinload(Proposta.items))
    result = await db.execute(stmt)
    return result.scalar_one()


@router.put("/{id}", response_model=PropostaResponse)
async def update_proposta(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    proposta_in: PropostaUpdate,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    stmt = select(Proposta).where(
        Proposta.id == id, 
        Proposta.empresa_id == current_user.empresa_id
    ).options(selectinload(Proposta.items))
    result = await db.execute(stmt)
    proposta = result.scalar_one_or_none()
    
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    update_data = proposta_in.model_dump(exclude_unset=True, exclude={"items"})
    for field, value in update_data.items():
        setattr(proposta, field, value)

    # Handle items if provided
    if proposta_in.items is not None:
        # Simple approach: delete existing items and recreate
        # In a more complex app, we would match IDs to update/delete/create
        from sqlalchemy import delete
        await db.execute(delete(ItemProposta).where(ItemProposta.proposta_id == proposta.id))
        
        total_value = 0
        for item_in in proposta_in.items:
            item = ItemProposta(
                **item_in.model_dump(),
                proposta_id=proposta.id
            )
            db.add(item)
            total_value += item.subtotal
        
        proposta.valor_total = total_value

    await db.commit()
    
    # Refresh with items
    stmt = select(Proposta).where(Proposta.id == proposta.id).options(selectinload(Proposta.items))
    result = await db.execute(stmt)
    return result.scalar_one()


@router.delete("/{id}")
async def delete_proposta(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    proposta = await db.get(Proposta, id)
    if not proposta or proposta.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    await db.delete(proposta)
    await db.commit()
    return {"ok": True}


@router.get("/{id}/pdf")
async def download_proposta_pdf(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Gera e faz o download da proposta comercial em formato PDF."""
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    from app.services.pdf import generate_proposal_pdf

    stmt = select(Proposta).where(
        Proposta.id == id,
        Proposta.empresa_id == current_user.empresa_id
    ).options(
        selectinload(Proposta.items),
        selectinload(Proposta.cliente),
        selectinload(Proposta.empresa),
        selectinload(Proposta.usuario)
    )
    result = await db.execute(stmt)
    proposta = result.scalar_one_or_none()
    
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
        
    try:
        pdf_bytes = generate_proposal_pdf(proposta)
        filename = f"proposta_{proposta.numero}.pdf"
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        print(f"Erro ao gerar PDF da proposta: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")


@router.post("/preview")
async def preview_proposta_pdf(
    proposta_in: PropostaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Gera um PDF em memória baseado no payload atual para preview (não salva no banco)."""
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    from app.services.pdf import generate_proposal_pdf
    from app.models.empresa import Empresa

    # 1. Fetch relations
    stmt_cliente = select(Cliente).where(
        Cliente.id == proposta_in.cliente_id,
        Cliente.empresa_id == current_user.empresa_id
    )
    cliente = (await db.execute(stmt_cliente)).scalar_one_or_none()
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    stmt_empresa = select(Empresa).where(Empresa.id == current_user.empresa_id)
    empresa = (await db.execute(stmt_empresa)).scalar_one_or_none()

    # 2. Build mock objects
    proposta_dict = proposta_in.model_dump(exclude={"items"})
    
    # Calculate total value from items
    total_value = sum(item.subtotal for item in proposta_in.items)
    
    validade_dias = proposta_dict.get("validade_dias") or 15
    if not proposta_dict.get("data_validade"):
        proposta_dict["data_validade"] = datetime.now() + timedelta(days=validade_dias)

    # Use a dummy UUID for the preview
    import uuid
    mock_id = uuid.uuid4()
    
    # Get max numero for realistic preview or just use 'Preview'
    proposta = Proposta(
        **proposta_dict,
        id=mock_id,
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        numero=0, # Just for preview
        valor_total=total_value
    )
    
    # Attach relationships manually so SQLAlchemy doesn't complain
    proposta.cliente = cliente
    proposta.empresa = empresa
    proposta.usuario = current_user
    
    mock_items = []
    for item_in in proposta_in.items:
        item = ItemProposta(
            **item_in.model_dump(),
            id=uuid.uuid4(),
            proposta_id=mock_id
        )
        mock_items.append(item)
    
    proposta.items = mock_items

    # 3. Generate PDF
    try:
        pdf_bytes = generate_proposal_pdf(proposta)
        filename = "preview.pdf"
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        print(f"Erro ao gerar Preview do PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar Preview: {str(e)}")
