from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timedelta, timezone

FUSO_BR = timezone(timedelta(hours=-3))

from app.database import get_db
from app.models.orcamento import Orcamento, ItemOrcamento, StatusOrcamento
from app.models.cliente import Cliente
from app.schemas.orcamento import (
    OrcamentoCreate, 
    OrcamentoUpdate, 
    OrcamentoResponse, 
    OrcamentoList,
    ItemOrcamentoCreate
)
from app.core.dependencies import get_current_active_user
from app.models.usuario import Usuario

router = APIRouter(prefix="/api/orcamentos", tags=["orcamentos"])


@router.get("", response_model=dict[str, Any])
async def list_orcamentos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    status: StatusOrcamento | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    stmt = select(Orcamento).where(Orcamento.empresa_id == current_user.empresa_id)
    count_stmt = select(func.count()).select_from(Orcamento).where(
        Orcamento.empresa_id == current_user.empresa_id
    )

    if status:
        stmt = stmt.where(Orcamento.status == status)
        count_stmt = count_stmt.where(Orcamento.status == status)

    if search:
        search_filter = or_(
            Orcamento.titulo.ilike(f"%{search}%"),
            # Orcamento.cliente.razao_social.ilike(f"%{search}%") # Requires join
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total = await db.scalar(count_stmt)
    
    # Load cliente for the list
    stmt = stmt.options(selectinload(Orcamento.cliente))
    stmt = stmt.order_by(Orcamento.numero.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    orcamentos = result.scalars().all()

    # Map to OrcamentoList schema manually if needed, or rely on response_model
    items = []
    for p in orcamentos:
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


@router.get("/{id}", response_model=OrcamentoResponse)
async def get_orcamento(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    stmt = select(Orcamento).where(
        Orcamento.id == id, 
        Orcamento.empresa_id == current_user.empresa_id
    ).options(
        selectinload(Orcamento.items),
        selectinload(Orcamento.cliente)
    )
    result = await db.execute(stmt)
    orcamento = result.scalar_one_or_none()
    
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orcamento não encontrada")
    
    return orcamento


@router.post("", response_model=OrcamentoResponse, status_code=status.HTTP_201_CREATED)
async def create_orcamento(
    *,
    db: AsyncSession = Depends(get_db),
    orcamento_in: OrcamentoCreate,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    # 1. Get next proposal number for the company
    result = await db.execute(
        select(func.max(Orcamento.numero)).where(Orcamento.empresa_id == current_user.empresa_id)
    )
    max_numero = result.scalar() or 0
    next_numero = max_numero + 1

    # 2. Create Orcamento
    orcamento_dict = orcamento_in.model_dump(exclude={"items"})
    
    # Calculate total value from items
    total_value = sum(item.subtotal for item in orcamento_in.items)
    
    # Set expiration date if not provided
    validade_dias = orcamento_dict.get("validade_dias") or 15
    if not orcamento_dict.get("data_validade"):
        orcamento_dict["data_validade"] = datetime.now(FUSO_BR) + timedelta(days=validade_dias)

    orcamento = Orcamento(
        **orcamento_dict,
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        numero=next_numero,
        valor_total=total_value,
        data_emissao=datetime.now(FUSO_BR)
    )
    
    db.add(orcamento)
    await db.flush() 
    
    # 2. Create Items
    for item_in in orcamento_in.items:
        item = ItemOrcamento(
            **item_in.model_dump(),
            orcamento_id=orcamento.id
        )
        db.add(item)
    
    await db.commit()
    
    # Refresh with items
    stmt = select(Orcamento).where(Orcamento.id == orcamento.id).options(selectinload(Orcamento.items))
    result = await db.execute(stmt)
    return result.scalar_one()


@router.put("/{id}", response_model=OrcamentoResponse)
async def update_orcamento(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    orcamento_in: OrcamentoUpdate,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    stmt = select(Orcamento).where(
        Orcamento.id == id, 
        Orcamento.empresa_id == current_user.empresa_id
    ).options(selectinload(Orcamento.items))
    result = await db.execute(stmt)
    orcamento = result.scalar_one_or_none()
    
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orcamento não encontrada")

    update_data = orcamento_in.model_dump(exclude_unset=True, exclude={"items"})
    for field, value in update_data.items():
        setattr(orcamento, field, value)

    # Handle items if provided
    if orcamento_in.items is not None:
        # Simple approach: delete existing items and recreate
        # In a more complex app, we would match IDs to update/delete/create
        from sqlalchemy import delete
        await db.execute(delete(ItemOrcamento).where(ItemOrcamento.orcamento_id == orcamento.id))
        
        total_value = 0
        for item_in in orcamento_in.items:
            item = ItemOrcamento(
                **item_in.model_dump(),
                orcamento_id=orcamento.id
            )
            db.add(item)
            total_value += item.subtotal
        
        orcamento.valor_total = total_value

    await db.commit()
    
    # Refresh with items
    stmt = select(Orcamento).where(Orcamento.id == orcamento.id).options(selectinload(Orcamento.items))
    result = await db.execute(stmt)
    return result.scalar_one()


@router.delete("/{id}")
async def delete_orcamento(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    orcamento = await db.get(Orcamento, id)
    if not orcamento or orcamento.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Orcamento não encontrada")

    await db.delete(orcamento)
    await db.commit()
    return {"ok": True}


@router.get("/{id}/pdf")
async def download_orcamento_pdf(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Gera e faz o download da orcamento comercial em formato PDF."""
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    from app.services.pdf import generate_proposal_pdf

    stmt = select(Orcamento).where(
        Orcamento.id == id,
        Orcamento.empresa_id == current_user.empresa_id
    ).options(
        selectinload(Orcamento.items),
        selectinload(Orcamento.cliente),
        selectinload(Orcamento.empresa),
        selectinload(Orcamento.usuario)
    )
    result = await db.execute(stmt)
    orcamento = result.scalar_one_or_none()
    
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orcamento não encontrada")
        
    try:
        pdf_bytes = generate_proposal_pdf(orcamento)
        filename = f"orcamento_{orcamento.numero}.pdf"
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        print(f"Erro ao gerar PDF da orcamento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")


@router.post("/preview")
async def preview_orcamento_pdf(
    orcamento_in: OrcamentoCreate,
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
        Cliente.id == orcamento_in.cliente_id,
        Cliente.empresa_id == current_user.empresa_id
    )
    cliente = (await db.execute(stmt_cliente)).scalar_one_or_none()
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    stmt_empresa = select(Empresa).where(Empresa.id == current_user.empresa_id)
    empresa = (await db.execute(stmt_empresa)).scalar_one_or_none()

    # 2. Build mock objects
    orcamento_dict = orcamento_in.model_dump(exclude={"items"})
    
    # Calculate total value from items
    total_value = sum(item.subtotal for item in orcamento_in.items)
    
    validade_dias = orcamento_dict.get("validade_dias") or 15
    if not orcamento_dict.get("data_validade"):
        orcamento_dict["data_validade"] = datetime.now() + timedelta(days=validade_dias)

    # Use a dummy UUID for the preview
    import uuid
    mock_id = uuid.uuid4()
    
    # Get max numero for realistic preview or just use 'Preview'
    orcamento = Orcamento(
        **orcamento_dict,
        id=mock_id,
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        numero=0, # Just for preview
        valor_total=total_value
    )
    
    # Attach relationships manually so SQLAlchemy doesn't complain
    orcamento.cliente = cliente
    orcamento.empresa = empresa
    orcamento.usuario = current_user
    
    mock_items = []
    for item_in in orcamento_in.items:
        item = ItemOrcamento(
            **item_in.model_dump(),
            id=uuid.uuid4(),
            orcamento_id=mock_id
        )
        mock_items.append(item)
    
    orcamento.items = mock_items

    # 3. Generate PDF
    try:
        pdf_bytes = generate_proposal_pdf(orcamento)
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

@router.post("/{id}/enviar-email")
async def enviar_orcamento_email(
    id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    from fastapi.concurrency import run_in_threadpool
    from app.services.email import send_email_sync

    stmt = select(Orcamento).where(
        Orcamento.id == id,
        Orcamento.empresa_id == current_user.empresa_id
    ).options(
        selectinload(Orcamento.cliente),
        selectinload(Orcamento.empresa)
    )
    result = await db.execute(stmt)
    orcamento = result.scalar_one_or_none()

    if not orcamento:
        raise HTTPException(status_code=404, detail="Orcamento não encontrado")
    if not orcamento.cliente or not orcamento.cliente.email:
        raise HTTPException(status_code=400, detail="Cliente não possui e-mail cadastrado")
    if not orcamento.empresa.smtp_host:
        raise HTTPException(status_code=400, detail="Configuração de SMTP da empresa incompleta. Verifique as configurações globais.")

    origin = request.headers.get("origin", "https://seu-dominio.com")
    link = f"{origin}/o/{orcamento.token_publico}"
    
    subject = f"Orçamento Comercial #{orcamento.numero} - {orcamento.empresa.razao_social}"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
        <h2 style="color: #4f46e5;">Olá, {orcamento.cliente.contato_nome or orcamento.cliente.razao_social}!</h2>
        <p>A empresa <strong>{orcamento.empresa.razao_social}</strong> enviou um orçamento comercial para você.</p>
        <p><strong>Título:</strong> {orcamento.titulo}</p>
        <div style="margin: 30px 0; text-align: center;">
            <a href="{link}" style="background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Visualizar Orçamento Completo</a>
        </div>
        <p>Se tiver qualquer dúvida, basta responder a este e-mail.</p>
        <hr style="border: 0; border-top: 1px solid #eaeaea; margin: 20px 0;" />
        <p style="font-size: 12px; color: #888; text-align: center;">Enviado via Painel Proposta</p>
    </div>
    """

    try:
        await run_in_threadpool(
            send_email_sync,
            empresa=orcamento.empresa,
            to_email=orcamento.cliente.email,
            subject=subject,
            html_content=html_content
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar e-mail: {str(e)}")

    return {"ok": True, "message": "E-mail enviado com sucesso"}

