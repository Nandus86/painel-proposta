from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str


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
    is_superuser: bool = False

    model_config = {"from_attributes": True}
