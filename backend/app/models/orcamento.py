import uuid
import enum
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func, Integer, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class StatusOrcamento(str, enum.Enum):
    RASCUNHO = "rascunho"
    ENVIADO = "enviado"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"
    VENCIDO = "vencido"


class Orcamento(Base):
    __tablename__ = "orcamentos"

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
    status: Mapped[StatusOrcamento] = mapped_column(
        Enum(StatusOrcamento), default=StatusOrcamento.RASCUNHO, nullable=False
    )
    
    data_emissao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    data_validade: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    validade_dias: Mapped[int] = mapped_column(Integer, default=15)
    
    valor_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    observacoes: Mapped[Optional[str]] = mapped_column(Text)
    condicoes_pagamento: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    visualizacoes: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    
    token_publico: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    assinatura_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    assinatura_data: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relacionamentos
    empresa = relationship("Empresa", backref="orcamentos")
    cliente = relationship("Cliente", backref="orcamentos")
    usuario = relationship("Usuario", backref="orcamentos")
    items: Mapped[List["ItemOrcamento"]] = relationship(
        "ItemOrcamento", back_populates="orcamento", cascade="all, delete-orphan"
    )
    proposta = relationship("Proposta", back_populates="orcamento", uselist=False)


class ItemOrcamento(Base):
    __tablename__ = "itens_orcamento"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    orcamento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orcamentos.id", ondelete="CASCADE"), nullable=False
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
    orcamento = relationship("Orcamento", back_populates="items")
    servico = relationship("Servico")
