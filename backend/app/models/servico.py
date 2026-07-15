import uuid
import enum
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func, Boolean, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TipoServico(str, enum.Enum):
    PRODUTO = "produto"
    SERVICO = "servico"
    RECORRENTE = "recorrente"


class Servico(Base):
    __tablename__ = "servicos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False
    )
    categoria_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categorias.id", ondelete="SET NULL")
    )
    
    tipo: Mapped[TipoServico] = mapped_column(
        Enum(TipoServico), default=TipoServico.SERVICO, nullable=False
    )
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao_padrao: Mapped[Optional[str]] = mapped_column(Text)
    preco_base: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    custo_base: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    instrucoes_ia: Mapped[Optional[str]] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relacionamentos
    empresa = relationship("Empresa", back_populates="servicos")
    categoria = relationship("Categoria", back_populates="servicos", lazy="joined")
