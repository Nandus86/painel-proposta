import uuid
import enum
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func, Integer, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.orcamento import Orcamento


class StatusProposta(str, enum.Enum):
    RASCUNHO = "rascunho"
    ENVIADA = "enviada"
    ACEITA = "aceita"
    RECUSADA = "recusada"
    EXPIRADA = "expirada"


class Proposta(Base):
    __tablename__ = "propostas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )
    
    numero: Mapped[int] = mapped_column(Integer, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[StatusProposta] = mapped_column(
        Enum(StatusProposta), default=StatusProposta.RASCUNHO, nullable=False
    )
    
    data_emissao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    data_validade: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    validade_dias: Mapped[int] = mapped_column(Integer, default=15)
    
    valor_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    observacoes: Mapped[Optional[str]] = mapped_column(Text)
    condicoes_pagamento: Mapped[Optional[str]] = mapped_column(Text)

    visualizacoes: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")

    orcamento_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orcamentos.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    token_publico: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    assinatura_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    assinatura_data: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relacionamentos
    empresa = relationship("Empresa", back_populates="propostas")
    cliente = relationship("Cliente", backref="propostas")
    usuario = relationship("Usuario", backref="propostas")
    orcamento = relationship("Orcamento", back_populates="proposta")
    items: Mapped[List["ItemProposta"]] = relationship(
        "ItemProposta", back_populates="proposta", cascade="all, delete-orphan"
    )


class ItemProposta(Base):
    __tablename__ = "itens_proposta"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    proposta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propostas.id", ondelete="CASCADE"), nullable=False
    )
    servico_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("servicos.id", ondelete="SET NULL")
    )
    
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(10, 2), default=1.0)
    preco_unitario: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    desconto: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    
    ordem: Mapped[int] = mapped_column(Integer, default=0)

    # Relacionamentos
    proposta = relationship("Proposta", back_populates="items")
    servico = relationship("Servico")
