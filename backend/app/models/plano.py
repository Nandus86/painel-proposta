from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, Integer, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Plano(Base):
    __tablename__ = "planos"

    slug: Mapped[str] = mapped_column(String(50), primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preco_mensal: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    preco_anual: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    moeda: Mapped[str] = mapped_column(String(3), default="BRL")
    max_usuarios: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_propostas_mes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_credits_limit: Mapped[int] = mapped_column(Integer, default=20)
    permite_dominio_proprio: Mapped[bool] = mapped_column(Boolean, default=False)
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    destaque: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
