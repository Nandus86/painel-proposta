from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    nome: str = Field(..., max_length=255)
    email: EmailStr
    senha: str = Field(..., max_length=128)
    empresa: str | None = Field(None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserInfo(BaseModel):
    id: str
    nome: str
    email: str
    cargo: str | None
    role: str
    empresa_id: str
    empresa_nome: str | None = None
    empresa_cor_marca: str | None = None
    empresa_plano: str | None = None
    empresa_plano_nome: str | None = None
    is_superuser: bool = False

    model_config = {"from_attributes": True}


class EsqueciSenhaRequest(BaseModel):
    email: EmailStr


class RedefinirSenhaRequest(BaseModel):
    token: str = Field(..., max_length=2048)
    senha: str = Field(..., max_length=128)


class AlterarSenhaRequest(BaseModel):
    senha_atual: str = Field(..., max_length=128)
    nova_senha: str = Field(..., max_length=128)
