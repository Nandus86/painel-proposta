import uuid
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
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


@router.post("/import/csv")
async def import_clientes_csv(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="O arquivo deve ser um CSV")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV sem cabeçalho")

    importados = 0
    erros = []

    for row_num, row in enumerate(reader, start=2):
        razao_social = row.get("razao_social") or row.get("nome") or row.get("Nome") or ""
        if not razao_social or not razao_social.strip():
            erros.append(f"Linha {row_num}: razão social/nome obrigatório")
            continue

        cliente = Cliente(
            empresa_id=current_user.empresa_id,
            razao_social=razao_social.strip(),
            nome_fantasia=(row.get("nome_fantasia") or row.get("fantasia") or "").strip() or None,
            cnpj=(row.get("cnpj") or row.get("CNPJ") or "").strip() or None,
            cpf=(row.get("cpf") or row.get("CPF") or "").strip() or None,
            email=(row.get("email") or row.get("Email") or "").strip() or None,
            telefone=(row.get("telefone") or row.get("fone") or row.get("Telefone") or "").strip() or None,
            contato_nome=(row.get("contato") or row.get("contato_nome") or "").strip() or None,
            contato_cargo=(row.get("cargo") or row.get("contato_cargo") or "").strip() or None,
            endereco=(row.get("endereco") or "").strip() or None,
            cidade=(row.get("cidade") or "").strip() or None,
            estado=(row.get("estado") or row.get("uf") or "").strip() or None,
            cep=(row.get("cep") or row.get("CEP") or "").strip() or None,
            observacoes=(row.get("observacoes") or "").strip() or None,
        )
        db.add(cliente)
        importados += 1

    await db.flush()

    return {
        "ok": True,
        "importados": importados,
        "erros": erros,
        "total_linhas": row_num - 1 if reader.line_num else 0,
    }
