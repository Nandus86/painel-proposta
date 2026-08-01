from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/painel_proposta"
    DATABASE_URL_SYNC: str = "postgresql+psycopg://postgres:postgres@localhost:5432/painel_proposta"

    # JWT
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o"

    # App
    APP_NAME: str = "Dekto"
    APP_VERSION: str = "1.0.0"
    CORS_ORIGINS: str = "http://localhost:5173"
    BASE_DOMAIN: str = "dekto.com"
    FRONTEND_URL: str = "http://localhost:5173"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Storage / MinIO
    STORAGE_PROVIDER: str = "local"
    MINIO_ENDPOINT: Optional[str] = None
    MINIO_ACCESS_KEY: Optional[str] = None
    MINIO_SECRET_KEY: Optional[str] = None
    MINIO_BUCKET_NAME: str = "painel-proposta"
    MINIO_SECURE: bool = False
    MINIO_PUBLIC_URL: Optional[str] = None


    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

if not settings.SECRET_KEY and settings.ENVIRONMENT != "development":
    raise RuntimeError("SECRET_KEY must be set in production")
if not settings.SECRET_KEY and settings.ENVIRONMENT == "development":
    settings.SECRET_KEY = "dev-secret-key-change-in-production"
