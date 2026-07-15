import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse, ClienteListResponse
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/clientes", tags=["Clientes"])


@router.get("", response_model=ClienteListResponse)
async def list_clientes(
    search: str = Query(None, description="Buscar por razão social, fantasia ou CNPJ"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List clients from the same company."""
    query = select(Cliente).where(Cliente.empresa_id == current_user.empresa_id)

    if search:
        query = query.where(
            (Cliente.razao_social.ilike(f"%{search}%"))
            | (Cliente.nome_fantasia.ilike(f"%{search}%"))
            | (Cliente.cnpj.ilike(f"%{search}%"))
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    result = await db.execute(
        query.order_by(Cliente.razao_social).offset(skip).limit(limit)
    )
    clientes = result.scalars().all()

    return ClienteListResponse(
        items=[
            ClienteResponse(
                id=str(c.id),
                empresa_id=str(c.empresa_id),
                razao_social=c.razao_social,
                nome_fantasia=c.nome_fantasia,
                cnpj=c.cnpj,
                cpf=c.cpf,
                email=c.email,
                telefone=c.telefone,
                contato_nome=c.contato_nome,
                contato_cargo=c.contato_cargo,
                endereco=c.endereco,
                cidade=c.cidade,
                estado=c.estado,
                cep=c.cep,
                observacoes=c.observacoes,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in clientes
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
async def create_cliente(
    data: ClienteCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new client."""
    cliente = Cliente(
        empresa_id=current_user.empresa_id,
        **data.model_dump(),
    )
    db.add(cliente)
    await db.flush()
    await db.refresh(cliente)

    return ClienteResponse(
        id=str(cliente.id),
        empresa_id=str(cliente.empresa_id),
        razao_social=cliente.razao_social,
        nome_fantasia=cliente.nome_fantasia,
        cnpj=cliente.cnpj,
        cpf=cliente.cpf,
        email=cliente.email,
        telefone=cliente.telefone,
        contato_nome=cliente.contato_nome,
        contato_cargo=cliente.contato_cargo,
        endereco=cliente.endereco,
        cidade=cliente.cidade,
        estado=cliente.estado,
        cep=cliente.cep,
        observacoes=cliente.observacoes,
        created_at=cliente.created_at,
        updated_at=cliente.updated_at,
    )


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def get_cliente(
    cliente_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get client details."""
    result = await db.execute(
        select(Cliente).where(
            Cliente.id == uuid.UUID(cliente_id),
            Cliente.empresa_id == current_user.empresa_id,
        )
    )
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    return ClienteResponse(
        id=str(cliente.id),
        empresa_id=str(cliente.empresa_id),
        razao_social=cliente.razao_social,
        nome_fantasia=cliente.nome_fantasia,
        cnpj=cliente.cnpj,
        cpf=cliente.cpf,
        email=cliente.email,
        telefone=cliente.telefone,
        contato_nome=cliente.contato_nome,
        contato_cargo=cliente.contato_cargo,
        endereco=cliente.endereco,
        cidade=cliente.cidade,
        estado=cliente.estado,
        cep=cliente.cep,
        observacoes=cliente.observacoes,
        created_at=cliente.created_at,
        updated_at=cliente.updated_at,
    )


@router.put("/{cliente_id}", response_model=ClienteResponse)
async def update_cliente(
    cliente_id: str,
    data: ClienteUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update client."""
    result = await db.execute(
        select(Cliente).where(
            Cliente.id == uuid.UUID(cliente_id),
            Cliente.empresa_id == current_user.empresa_id,
        )
    )
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cliente, field, value)

    await db.flush()
    await db.refresh(cliente)

    return ClienteResponse(
        id=str(cliente.id),
        empresa_id=str(cliente.empresa_id),
        razao_social=cliente.razao_social,
        nome_fantasia=cliente.nome_fantasia,
        cnpj=cliente.cnpj,
        cpf=cliente.cpf,
        email=cliente.email,
        telefone=cliente.telefone,
        contato_nome=cliente.contato_nome,
        contato_cargo=cliente.contato_cargo,
        endereco=cliente.endereco,
        cidade=cliente.cidade,
        estado=cliente.estado,
        cep=cliente.cep,
        observacoes=cliente.observacoes,
        created_at=cliente.created_at,
        updated_at=cliente.updated_at,
    )


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cliente(
    cliente_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete client."""
    result = await db.execute(
        select(Cliente).where(
            Cliente.id == uuid.UUID(cliente_id),
            Cliente.empresa_id == current_user.empresa_id,
        )
    )
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    await db.delete(cliente)
    await db.flush()
