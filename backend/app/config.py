from pydantic_settings import BaseSettings
from typing import Optional


# Valores de exemplo que nunca podem ir para produção
_INSECURE_SECRET_KEYS = {
    "",
    "super-secret-key-change-in-production",
    "dev-secret-key-change-in-production",
    "troque-esta-chave",
}


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/painel_proposta"
    DATABASE_URL_SYNC: str = "postgresql+psycopg://postgres:postgres@localhost:5432/painel_proposta"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 10

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
    # URL pública do painel (usada nos links enviados aos clientes), ex.: https://app.dekto.com
    FRONTEND_URL: str = "http://localhost:5173"
    # Quando true, links públicos usam o domínio próprio / subdomínio da empresa
    # (exige DNS wildcard + certificado configurados no proxy).
    PUBLIC_LINKS_USE_TENANT_DOMAIN: bool = False
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    MAX_UPLOAD_MB: int = 5

    # E-mail do sistema (recuperação de senha, boas-vindas e avisos aos vendedores).
    # Independente do SMTP que cada empresa usa para enviar propostas.
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None  # padrão: SMTP_USER
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30

    # Rotinas periódicas (vencimento de documentos e avisos)
    JOBS_ENABLED: bool = True
    JOBS_INTERVAL_MINUTES: int = 60
    AVISO_VENCIMENTO_DIAS: int = 3

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
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() not in ("development", "dev", "local", "test")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

if settings.is_production:
    if settings.SECRET_KEY in _INSECURE_SECRET_KEYS or len(settings.SECRET_KEY) < 32:
        raise RuntimeError(
            "SECRET_KEY ausente ou insegura. Defina uma chave aleatória com pelo menos 32 caracteres "
            "(ex.: `openssl rand -hex 32`). ATENÇÃO: ela também cifra senhas SMTP e tokens salvos no banco; "
            "não a troque depois de entrar em produção."
        )
elif not settings.SECRET_KEY:
    settings.SECRET_KEY = "dev-secret-key-change-in-production"
