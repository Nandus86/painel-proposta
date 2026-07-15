import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False
    )
    razao_social: Mapped[str] = mapped_column(String(255), nullable=False)
    nome_fantasia: Mapped[Optional[str]] = mapped_column(String(255))
    cnpj: Mapped[Optional[str]] = mapped_column(String(18))
    cpf: Mapped[Optional[str]] = mapped_column(String(14))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    telefone: Mapped[Optional[str]] = mapped_column(String(20))
    contato_nome: Mapped[Optional[str]] = mapped_column(String(255))
    contato_cargo: Mapped[Optional[str]] = mapped_column(String(100))
    endereco: Mapped[Optional[str]] = mapped_column(String(500))
    cidade: Mapped[Optional[str]] = mapped_column(String(100))
    estado: Mapped[Optional[str]] = mapped_column(String(2))
    cep: Mapped[Optional[str]] = mapped_column(String(10))
    observacoes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    empresa = relationship("Empresa", back_populates="clientes")
