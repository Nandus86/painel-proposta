import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SistemaConfig(Base):
    __tablename__ = "sistema_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    
    # AI Config
    openrouter_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    openrouter_model: Mapped[str] = mapped_column(String(255), default="google/gemini-2.5-flash")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def has_openrouter_key(self) -> bool:
        return bool(self.openrouter_key)
