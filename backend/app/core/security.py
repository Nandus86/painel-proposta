import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        import bcrypt as bcrypt_lib
        return bcrypt_lib.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def get_fernet() -> Fernet:
    """Gera uma instância de Fernet a partir da SECRET_KEY da aplicação."""
    # Garante que a chave tenha exatamente 32 bytes usando hash SHA-256
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    key_b64 = base64.urlsafe_b64encode(key)
    return Fernet(key_b64)


def encrypt_data(data: str) -> str:
    """Criptografa uma string usando Fernet."""
    if not data:
        return ""
    try:
        f = get_fernet()
        return f.encrypt(data.encode()).decode()
    except Exception as e:
        print(f"Erro ao criptografar dados: {e}")
        return ""


def decrypt_data(token: str) -> str:
    """Descriptografa um token Fernet para a string original."""
    if not token:
        return ""
    try:
        f = get_fernet()
        return f.decrypt(token.encode()).decode()
    except Exception as e:
        print(f"Erro ao descriptografar dados: {e}")
        return ""
