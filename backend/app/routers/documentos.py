"""Rotas compartilhadas de Propostas e Orçamentos.

Os dois documentos têm a mesma estrutura (cabeçalho + itens); este módulo monta
um router completo a partir de um `DocKind`, evitando manter duas cópias do código.
"""
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Any, Callable, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_active_user
from app.database import get_db
from app.models.cliente import Cliente
from app.models.empresa import Empresa
from app.models.notificacao import Notificacao
from app.models.servico import Servico
from app.models.usuario import Usuario
from app.services.links import build_public_url
from app.services.storage import storage_service

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocKind:
    model: Any
    item_model: Any
    item_fk: str
    status_enum: Any
    status_enviado: Any
    status_vencido: Any
    status_finais: tuple  # status que não podem ser definidos na criação (aceite/recusa)
    label: str  # "Proposta" / "Orçamento"
    nao_encontrado: str
    is_orcamento: bool
    create_schema: Any
    update_schema: Any
    response_schema: Any
    limit_dependency: Callable


def _calc_items(items_in) -> tuple[list[dict], float]:
    """Recalcula subtotais no servidor (o cliente não define o valor final)."""
    items, total = [], 0.0
    for idx, item in enumerate(items_in):
        data = item.model_dump()
        qtd = float(data.get("quantidade") or 0)
        preco = float(data.get("preco_unitario") or 0)
        desconto = float(data.get("desconto") or 0)
        if qtd < 0 or preco < 0 or desconto < 0:
            raise HTTPException(status_code=400, detail="Quantidade, preço e desconto não podem ser negativos.")
        subtotal = round(max(qtd * preco - desconto, 0), 2)
        data["subtotal"] = subtotal
        data["ordem"] = data.get("ordem") or idx
        items.append(data)
        total += subtotal
    return items, round(total, 2)


async def _validar_referencias(db: AsyncSession, empresa_id, cliente_id: Optional[UUID], items: list[dict]) -> Optional[Cliente]:
    """Garante que cliente e serviços pertencem à empresa do usuário."""
    cliente = None
    if cliente_id is not None:
        cliente = (await db.execute(
            select(Cliente).where(Cliente.id == cliente_id, Cliente.empresa_id == empresa_id)
        )).scalar_one_or_none()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

    servico_ids = {i["servico_id"] for i in items if i.get("servico_id")}
    if servico_ids:
        encontrados = (await db.execute(
            select(Servico.id).where(Servico.id.in_(servico_ids), Servico.empresa_id == empresa_id)
        )).scalars().all()
        if len(set(encontrados)) != len(servico_ids):
            raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return cliente


async def render_pdf(doc, kind: DocKind) -> bytes:
    logo = await storage_service.get_data_uri(getattr(doc.empresa, "logo_url", None))
    return await run_in_threadpool(_generate_pdf, doc, kind.label, logo)


def _generate_pdf(doc, label: str, logo: Optional[str]) -> bytes:
    from app.services.pdf import generate_proposal_pdf
    return generate_proposal_pdf(doc, tipo_doc=label, logo_src=logo)


def _pdf_response(pdf_bytes: bytes, filename: str, inline: bool) -> StreamingResponse:
    disposition = "inline" if inline else "attachment"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


def build_router(kind: DocKind, prefix: str, tags: list[str]) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=tags)
    Model, Item = kind.model, kind.item_model
    slug = "orcamento" if kind.is_orcamento else "proposta"

    async def _get_doc(db: AsyncSession, id: UUID, empresa_id, *extra_loads):
        stmt = select(Model).where(Model.id == id, Model.empresa_id == empresa_id).options(
            selectinload(Model.items), *[selectinload(getattr(Model, r)) for r in extra_loads]
        )
        doc = (await db.execute(stmt)).scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail=kind.nao_encontrado)
        return doc

    async def _reload(db: AsyncSession, id: UUID):
        db.expire_all()
        stmt = select(Model).where(Model.id == id).options(selectinload(Model.items))
        return (await db.execute(stmt)).scalar_one()

    @router.get("", response_model=dict[str, Any])
    async def list_documentos(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        search: str | None = None,
        status: kind.status_enum | None = None,  # type: ignore[valid-type]
        db: AsyncSession = Depends(get_db),
        current_user: Usuario = Depends(get_current_active_user),
    ) -> Any:
        filtros = [Model.empresa_id == current_user.empresa_id]
        if status:
            filtros.append(Model.status == status)
        if search and search.strip():
            termo = f"%{search.strip()}%"
            filtros.append(or_(
                Model.titulo.ilike(termo),
                Cliente.razao_social.ilike(termo),
                Cliente.nome_fantasia.ilike(termo),
            ))

        base = select(Model).join(Cliente, Cliente.id == Model.cliente_id).where(*filtros)
        total = await db.scalar(select(func.count()).select_from(base.subquery()))

        stmt = base.options(selectinload(Model.cliente)).order_by(Model.numero.desc()).offset(skip).limit(limit)
        docs = (await db.execute(stmt)).scalars().all()

        items = [{
            "id": d.id,
            "numero": d.numero,
            "titulo": d.titulo,
            "cliente_nome": d.cliente.razao_social,
            "status": d.status,
            "valor_total": d.valor_total,
            "data_emissao": d.data_emissao,
            "data_validade": d.data_validade,
            "token_publico": d.token_publico,
            "visualizacoes": d.visualizacoes,
        } for d in docs]

        return {"items": items, "total": total, "skip": skip, "limit": limit}

    @router.get("/{id}", response_model=kind.response_schema)
    async def get_documento(
        id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: Usuario = Depends(get_current_active_user),
    ) -> Any:
        return await _get_doc(db, id, current_user.empresa_id, "cliente")

    @router.post("", response_model=kind.response_schema, status_code=201)
    async def create_documento(
        doc_in: kind.create_schema,  # type: ignore[valid-type]
        db: AsyncSession = Depends(get_db),
        current_user: Usuario = Depends(get_current_active_user),
        _limit: None = Depends(kind.limit_dependency),
    ) -> Any:
        if not doc_in.items:
            raise HTTPException(status_code=400, detail="Adicione pelo menos um item.")
        items, total = _calc_items(doc_in.items)
        await _validar_referencias(db, current_user.empresa_id, doc_in.cliente_id, items)

        empresa = await db.get(Empresa, current_user.empresa_id)
        dados = doc_in.model_dump(exclude={"items"})
        if dados.get("status") in kind.status_finais:
            dados["status"] = kind.status_enum.RASCUNHO
        if not dados.get("validade_dias"):
            dados["validade_dias"] = (empresa.validade_padrao_dias if empresa else None) or 30
        agora = datetime.now(timezone.utc)
        if not dados.get("data_validade"):
            dados["data_validade"] = agora + timedelta(days=dados["validade_dias"])

        # Serializa a numeração por empresa (evita números duplicados em criações simultâneas)
        await db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": f"{slug}:{current_user.empresa_id}"})
        max_numero = await db.scalar(
            select(func.max(Model.numero)).where(Model.empresa_id == current_user.empresa_id)
        )

        doc = Model(
            **dados,
            empresa_id=current_user.empresa_id,
            usuario_id=current_user.id,
            numero=(max_numero or 0) + 1,
            valor_total=total,
            data_emissao=agora,
        )
        db.add(doc)
        await db.flush()
        for item in items:
            db.add(Item(**item, **{kind.item_fk: doc.id}))
        await db.commit()
        return await _reload(db, doc.id)

    @router.put("/{id}", response_model=kind.response_schema)
    async def update_documento(
        id: UUID,
        doc_in: kind.update_schema,  # type: ignore[valid-type]
        db: AsyncSession = Depends(get_db),
        current_user: Usuario = Depends(get_current_active_user),
    ) -> Any:
        doc = await _get_doc(db, id, current_user.empresa_id)
        dados = doc_in.model_dump(exclude_unset=True, exclude={"items"})

        items = None
        if doc_in.items is not None:
            if not doc_in.items:
                raise HTTPException(status_code=400, detail="Adicione pelo menos um item.")
            items, total = _calc_items(doc_in.items)
        await _validar_referencias(db, current_user.empresa_id, dados.get("cliente_id"), items or [])

        if dados.get("cliente_id") is None:
            dados.pop("cliente_id", None)
        if "validade_dias" in dados and "data_validade" not in dados and dados["validade_dias"]:
            inicio = doc.data_emissao or datetime.now(timezone.utc)
            dados["data_validade"] = inicio + timedelta(days=dados["validade_dias"])

        for field, value in dados.items():
            setattr(doc, field, value)

        # Prazo prorrogado: documento vencido volta a ficar disponível para o cliente
        if (
            "status" not in dados
            and doc.status == kind.status_vencido
            and doc.data_validade
            and doc.data_validade > datetime.now(timezone.utc)
        ):
            doc.status = kind.status_enviado

        if items is not None:
            await db.execute(delete(Item).where(getattr(Item, kind.item_fk) == doc.id))
            for item in items:
                db.add(Item(**item, **{kind.item_fk: doc.id}))
            doc.valor_total = total

        await db.commit()
        return await _reload(db, doc.id)

    @router.delete("/{id}")
    async def delete_documento(
        id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: Usuario = Depends(get_current_active_user),
    ) -> Any:
        doc = await db.get(Model, id)
        if not doc or doc.empresa_id != current_user.empresa_id:
            raise HTTPException(status_code=404, detail=kind.nao_encontrado)
        await db.execute(delete(Notificacao).where(Notificacao.referencia_id == doc.id))
        await db.delete(doc)
        await db.commit()
        return {"ok": True}

    @router.get("/{id}/pdf")
    async def download_pdf(
        id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: Usuario = Depends(get_current_active_user),
    ):
        doc = await _get_doc(db, id, current_user.empresa_id, "cliente", "empresa", "usuario")
        try:
            pdf = await render_pdf(doc, kind)
        except Exception:
            logger.exception("Erro ao gerar PDF de %s %s", slug, id)
            raise HTTPException(status_code=500, detail="Não foi possível gerar o PDF.")
        return _pdf_response(pdf, f"{slug}_{doc.numero}.pdf", inline=False)

    @router.post("/preview")
    async def preview_pdf(
        doc_in: kind.create_schema,  # type: ignore[valid-type]
        db: AsyncSession = Depends(get_db),
        current_user: Usuario = Depends(get_current_active_user),
    ):
        """Gera o PDF do payload atual sem salvar no banco."""
        items, total = _calc_items(doc_in.items)
        cliente = await _validar_referencias(db, current_user.empresa_id, doc_in.cliente_id, items)
        empresa = await db.get(Empresa, current_user.empresa_id)

        dados = doc_in.model_dump(exclude={"items"})
        agora = datetime.now(timezone.utc)
        if not dados.get("data_validade"):
            dados["data_validade"] = agora + timedelta(days=dados.get("validade_dias") or 30)

        mock_id = uuid.uuid4()
        doc = Model(**dados, id=mock_id, empresa_id=current_user.empresa_id, usuario_id=current_user.id,
                    numero=0, valor_total=total, data_emissao=agora)
        doc.cliente = cliente
        doc.empresa = empresa
        doc.usuario = current_user
        doc.items = [Item(**i, id=uuid.uuid4(), **{kind.item_fk: mock_id}) for i in items]
        # Objeto apenas em memória: não deve ser persistido pelo commit da sessão
        if doc in db:
            db.expunge(doc)

        try:
            pdf = await render_pdf(doc, kind)
        except Exception:
            logger.exception("Erro ao gerar preview de %s", slug)
            raise HTTPException(status_code=500, detail="Não foi possível gerar a pré-visualização.")
        finally:
            await db.rollback()
        return _pdf_response(pdf, "preview.pdf", inline=True)

    @router.post("/{id}/enviar-email")
    async def enviar_email(
        id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: Usuario = Depends(get_current_active_user),
    ):
        from app.services.email import get_email_content, send_email_sync, smtp_configurado, smtp_error_message

        doc = await _get_doc(db, id, current_user.empresa_id, "cliente", "empresa", "usuario")
        if not doc.cliente or not doc.cliente.email:
            raise HTTPException(status_code=400, detail="O cliente não possui e-mail cadastrado.")
        if not smtp_configurado(doc.empresa):
            raise HTTPException(
                status_code=400,
                detail="Configure o SMTP (host, porta, usuário e senha) em Configurações antes de enviar e-mails.",
            )

        link = build_public_url(doc.empresa, doc.token_publico, kind.is_orcamento)
        subject, html_content = get_email_content(doc.empresa, doc, link, is_orcamento=kind.is_orcamento)

        try:
            await run_in_threadpool(
                send_email_sync,
                empresa=doc.empresa,
                to_email=doc.cliente.email,
                subject=subject,
                html_content=html_content,
                reply_to=doc.usuario.email if doc.usuario else None,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Não foi possível enviar o e-mail: {smtp_error_message(e)}")

        if doc.status == kind.status_enum.RASCUNHO:
            doc.status = kind.status_enviado
            await db.commit()

        return {"ok": True, "message": "E-mail enviado com sucesso"}

    @router.post("/{id}/enviar-whatsapp")
    async def enviar_whatsapp(
        id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: Usuario = Depends(get_current_active_user),
    ):
        from app.models.sistema_config import SistemaConfig
        from app.services.whatsapp import send_text
        from app.services.email import build_email_variables, replace_variables

        doc = await _get_doc(db, id, current_user.empresa_id, "cliente", "empresa", "usuario")
        if not doc.cliente or not doc.cliente.telefone:
            raise HTTPException(status_code=400, detail="O cliente não possui telefone/WhatsApp cadastrado.")
        if not (doc.empresa.whatsapp_conectado or doc.empresa.whatsapp_status == 'connected'):
            raise HTTPException(
                status_code=400,
                detail="WhatsApp não está conectado. Conecte seu WhatsApp em Integrações antes de enviar.",
            )

        link = build_public_url(doc.empresa, doc.token_publico, kind.is_orcamento)
        variables = build_email_variables(doc.empresa, doc, is_orcamento=kind.is_orcamento)
        variables["link_proposta" if not kind.is_orcamento else "link_orcamento"] = link

        tipo_doc = "orçamento" if kind.is_orcamento else "proposta"
        artigo = "o" if kind.is_orcamento else "a"
        numero_str = f" #{doc.numero}" if getattr(doc, "numero", None) else ""
        msg_padrao = doc.empresa.whatsapp_mensagem_padrao or (
            f"Olá {{{{cliente_contato_nome}}}}! Segue {artigo} {tipo_doc}{numero_str} - *{{{{proposta_titulo}}}}* no valor de {{{{proposta_valor_total}}}}.\n\nAcesse pelo link: {link}"
        )
        msg_texto = replace_variables(msg_padrao, variables)

        sc = await db.get(SistemaConfig, 1)
        if not sc:
            sc = SistemaConfig(id=1)
            db.add(sc)

        try:
            await send_text(doc.empresa, sc, doc.cliente.telefone, msg_texto)
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp: {e}")
            raise HTTPException(status_code=400, detail=str(e))

        if doc.status == kind.status_enum.RASCUNHO:
            doc.status = kind.status_enviado
            await db.commit()

        return {"ok": True, "message": "Mensagem enviada com sucesso via WhatsApp"}

    return router

