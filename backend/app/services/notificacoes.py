"""Notificações do painel e rotina periódica de vencimento de propostas/orçamentos."""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import exists, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.notificacao import Notificacao
from app.models.orcamento import Orcamento, StatusOrcamento
from app.models.proposta import Proposta, StatusProposta

logger = logging.getLogger(__name__)


def descrever_documento(doc) -> tuple[str, str]:
    """(rótulo legível, link interno do editor) para uma proposta ou orçamento."""
    if isinstance(doc, Orcamento):
        return f"Orçamento #{doc.numero}", f"/orcamentos/{doc.id}/edit"
    return f"Proposta #{doc.numero}", f"/propostas/{doc.id}/edit"


async def notificar(
    db: AsyncSession,
    *,
    empresa_id: uuid.UUID,
    usuario_id: uuid.UUID,
    tipo: str,
    titulo: str,
    mensagem: Optional[str] = None,
    link: Optional[str] = None,
    referencia_id: Optional[uuid.UUID] = None,
    unica: bool = False,
) -> bool:
    """Cria uma notificação. Com `unica=True`, não repete o mesmo tipo para a mesma referência."""
    if unica and referencia_id is not None:
        ja_existe = await db.scalar(
            select(exists().where(Notificacao.referencia_id == referencia_id, Notificacao.tipo == tipo))
        )
        if ja_existe:
            return False
    db.add(Notificacao(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        tipo=tipo,
        titulo=titulo[:255],
        mensagem=mensagem,
        link=link,
        referencia_id=referencia_id,
    ))
    return True


_DOCS = (
    (Proposta, StatusProposta.ENVIADA, StatusProposta.EXPIRADA, "Proposta", "/propostas"),
    (Orcamento, StatusOrcamento.ENVIADO, StatusOrcamento.VENCIDO, "Orçamento", "/orcamentos"),
)


async def processar_vencimentos(db: AsyncSession, agora: Optional[datetime] = None) -> dict:
    """Marca como vencidos os documentos enviados fora da validade e avisa os que vencem em breve.

    Idempotente e protegida por advisory lock: pode rodar em vários workers ao mesmo tempo.
    """
    got_lock = await db.scalar(text("SELECT pg_try_advisory_xact_lock(hashtext('rotina_vencimentos'))"))
    if not got_lock:
        return {"executada": False}

    agora = agora or datetime.now(timezone.utc)
    limite_aviso = agora + timedelta(days=settings.AVISO_VENCIMENTO_DIAS)
    resumo = {"executada": True, "vencidos": 0, "avisos_vencimento": 0}

    for Model, status_enviado, status_vencido, rotulo, rota in _DOCS:
        vencidos = (await db.execute(
            update(Model)
            .where(Model.status == status_enviado, Model.data_validade.is_not(None), Model.data_validade < agora)
            .values(status=status_vencido)
            .returning(Model.id, Model.empresa_id, Model.usuario_id, Model.numero, Model.titulo)
        )).all()
        for doc_id, empresa_id, usuario_id, numero, titulo in vencidos:
            await notificar(
                db, empresa_id=empresa_id, usuario_id=usuario_id, tipo="vencida",
                titulo=f"{rotulo} #{numero} venceu",
                mensagem=f"\"{titulo}\" passou da validade sem resposta do cliente.",
                link=f"{rota}/{doc_id}/edit", referencia_id=doc_id, unica=True,
            )
        resumo["vencidos"] += len(vencidos)

        a_vencer = (await db.execute(
            select(Model.id, Model.empresa_id, Model.usuario_id, Model.numero, Model.titulo, Model.data_validade)
            .where(Model.status == status_enviado, Model.data_validade >= agora, Model.data_validade <= limite_aviso)
        )).all()
        for doc_id, empresa_id, usuario_id, numero, titulo, validade in a_vencer:
            dias = max((validade - agora).days, 0)
            prazo = "hoje" if dias == 0 else ("amanhã" if dias == 1 else f"em {dias} dias")
            criada = await notificar(
                db, empresa_id=empresa_id, usuario_id=usuario_id, tipo="vencendo",
                titulo=f"{rotulo} #{numero} vence {prazo}",
                mensagem=f"\"{titulo}\" ainda não foi respondida pelo cliente. Que tal fazer um follow-up?",
                link=f"{rota}/{doc_id}/edit", referencia_id=doc_id, unica=True,
            )
            resumo["avisos_vencimento"] += int(criada)

    await db.commit()
    if resumo["vencidos"] or resumo["avisos_vencimento"]:
        logger.info("Rotina de vencimentos: %s", resumo)
    return resumo


async def loop_rotinas(session_factory) -> None:
    """Executa as rotinas periodicamente enquanto a API estiver no ar."""
    await asyncio.sleep(30)  # deixa a API terminar de subir
    while True:
        try:
            async with session_factory() as db:
                await processar_vencimentos(db)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Falha na rotina de vencimentos")
        await asyncio.sleep(max(settings.JOBS_INTERVAL_MINUTES, 1) * 60)
