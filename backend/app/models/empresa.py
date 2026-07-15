import uuid
from typing import Optional
from datetime import datetime, date
from sqlalchemy import String, Text, DateTime, Date, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    razao_social: Mapped[str] = mapped_column(String(255), nullable=False)
    nome_fantasia: Mapped[Optional[str]] = mapped_column(String(255))
    cnpj: Mapped[str] = mapped_column(String(18), unique=True, nullable=False)
    inscricao_estadual: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    telefone: Mapped[Optional[str]] = mapped_column(String(20))
    endereco: Mapped[Optional[str]] = mapped_column(String(500))
    cidade: Mapped[Optional[str]] = mapped_column(String(100))
    estado: Mapped[Optional[str]] = mapped_column(String(2))
    cep: Mapped[Optional[str]] = mapped_column(String(10))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    observacoes: Mapped[Optional[str]] = mapped_column(Text)

    # Setup e Customização
    pais: Mapped[Optional[str]] = mapped_column(String(100))
    fuso_horario: Mapped[Optional[str]] = mapped_column(String(100))
    moeda: Mapped[Optional[str]] = mapped_column(String(10))
    idioma: Mapped[Optional[str]] = mapped_column(String(10))
    setor: Mapped[Optional[str]] = mapped_column(String(100))
    cor_marca: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Domínios
    subdominio: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    dominio_personalizado: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    
    # Integrações de Comunicação
    whatsapp_conectado: Mapped[bool] = mapped_column(default=False, server_default="false")
    telegram_conectado: Mapped[bool] = mapped_column(default=False, server_default="false")
    
    # Pagamentos (Stripe/PayTR)
    stripe_publishable_key: Mapped[Optional[str]] = mapped_column(String(255))
    stripe_secret_key: Mapped[Optional[str]] = mapped_column(String(255))
    pagamento_modo_teste: Mapped[bool] = mapped_column(default=True, server_default="true")

    # Controle SuperAdmin (Assinatura / Acesso)
    plano: Mapped[str] = mapped_column(String(50), default="gratuito", server_default="gratuito")
    status_pagamento: Mapped[str] = mapped_column(String(50), default="em_dia", server_default="em_dia")
    ativo: Mapped[bool] = mapped_column(default=True, server_default="true")

    # Configurações
    prefixo_proposta: Mapped[str] = mapped_column(String(10), default="PROP")
    validade_padrao_dias: Mapped[int] = mapped_column(default=30)
    modelo_proposta_padrao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_credits_used_today: Mapped[int] = mapped_column(Integer, default=0)
    ai_credits_limit: Mapped[int] = mapped_column(Integer, default=20)
    ai_credits_last_reset: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Configurações de SMTP (E-mail)
    smtp_host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    smtp_user: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    smtp_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    @property
    def has_smtp_password(self) -> bool:
        return bool(self.smtp_password)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relacionamentos
    usuarios = relationship("Usuario", back_populates="empresa", lazy="selectin")
    clientes = relationship("Cliente", back_populates="empresa", lazy="selectin")
    categorias = relationship("Categoria", back_populates="empresa", lazy="selectin")
    servicos = relationship("Servico", back_populates="empresa", lazy="selectin")
    propostas = relationship("Proposta", back_populates="empresa", lazy="selectin")
    logs_admin = relationship("LogAdmin", back_populates="empresa", lazy="selectin", cascade="all, delete-orphan")
