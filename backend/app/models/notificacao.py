import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Notificacao(Base):
    """Aviso exibido no sino do painel (cliente abriu/aceitou documento, vencimentos...)."""

    __tablename__ = "notificacoes"
    __table_args__ = (
        Index("ix_notificacoes_usuario_lida", "usuario_id", "lida", "created_at"),
        Index("ix_notificacoes_referencia", "referencia_id", "tipo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    # visualizada | aceita | vencendo | vencida
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    mensagem: Mapped[Optional[str]] = mapped_column(Text)
    link: Mapped[Optional[str]] = mapped_column(String(500))
    # id da proposta/orçamento de origem (evita avisos duplicados)
    referencia_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    lida: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
