import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    password_reset_token_valid,
    verify_password,
)
from app.database import get_db
from app.models.empresa import Empresa
from app.models.plano import Plano
from app.models.usuario import UserRole, Usuario
from app.schemas.auth import (
    AlterarSenhaRequest,
    EsqueciSenhaRequest,
    LoginRequest,
    RedefinirSenhaRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserInfo,
)
from app.services import email as email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])

MIN_PASSWORD_LENGTH = 8


def _issue_tokens(user: Usuario) -> TokenResponse:
    ver = user.token_version or 0
    access_token = create_access_token(
        data={"sub": str(user.id), "empresa_id": str(user.empresa_id), "role": user.role.value, "ver": ver}
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id), "ver": ver})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def _validar_nova_senha(senha: str) -> None:
    if len(senha) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"A senha deve ter pelo menos {MIN_PASSWORD_LENGTH} caracteres.")


def _enviar_email_sistema(to: str, subject: str, html: str) -> None:
    """Executado em background: falhas só vão para o log."""
    try:
        email_service.send_system_email(to, subject, html)
    except Exception:
        logger.exception("Falha ao enviar e-mail do sistema para %s", to)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, background: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Cadastra um novo usuário administrador e cria a empresa dele."""
    email = data.email.strip().lower()
    nome = data.nome.strip()
    if not nome:
        raise HTTPException(status_code=400, detail="Informe seu nome.")
    _validar_nova_senha(data.senha)

    existing = await db.execute(select(Usuario.id).where(func.lower(Usuario.email) == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já está em uso.")

    nome_empresa = (data.empresa or "").strip() or f"Empresa de {nome}"
    nova_empresa = Empresa(
        razao_social=nome_empresa[:255],
        nome_fantasia=(data.empresa or "").strip()[:255] or None,
        # CNPJ é obrigatório e único: placeholder até o cliente preencher no assistente
        cnpj=f"TMP-{uuid.uuid4().hex[:14]}",
    )
    db.add(nova_empresa)
    await db.flush()

    novo_usuario = Usuario(
        empresa_id=nova_empresa.id,
        nome=nome,
        email=email,
        senha_hash=get_password_hash(data.senha),
        role=UserRole.ADMIN,
        cargo="Administrador",
        token_version=0,
    )
    db.add(novo_usuario)
    await db.commit()

    if email_service.system_smtp_configurado():
        html = email_service.render_system_email(
            f"Bem-vindo(a) ao {settings.APP_NAME}!",
            [
                f"Olá, {nome}!",
                f"Sua conta para {nome_empresa} foi criada. Conclua o assistente de configuração para "
                "cadastrar sua marca, seus serviços e começar a enviar propostas.",
            ],
            "Acessar o painel",
            settings.FRONTEND_URL,
        )
        background.add_task(_enviar_email_sistema, email, f"Bem-vindo(a) ao {settings.APP_NAME}", html)

    return _issue_tokens(novo_usuario)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Autentica o usuário e devolve os tokens JWT."""
    result = await db.execute(
        select(Usuario)
        .where(func.lower(Usuario.email) == data.email.strip().lower())
        .options(selectinload(Usuario.empresa))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.senha, user.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos")

    if not user.ativo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário desativado. Contate o administrador.")

    if not user.empresa or not user.empresa.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Empresa bloqueada. Contate o administrador do sistema.",
        )

    user.ultimo_login = datetime.now(timezone.utc)
    await db.commit()

    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Gera um novo par de tokens a partir do refresh token."""
    payload = decode_token(data.refresh_token)
    if payload is None or payload.get("type") != "refresh" or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

    result = await db.execute(
        select(Usuario).where(Usuario.id == user_id).options(selectinload(Usuario.empresa))
    )
    user = result.scalar_one_or_none()

    if not user or not user.ativo or payload.get("ver", 0) != (user.token_version or 0):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão expirada. Faça login novamente.")
    if not user.empresa or not user.empresa.ativo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Empresa bloqueada.")

    return _issue_tokens(user)


@router.post("/esqueci-senha")
async def esqueci_senha(data: EsqueciSenhaRequest, background: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Envia o link de redefinição de senha. A resposta é sempre a mesma, exista ou não a conta."""
    if not email_service.system_smtp_configurado():
        raise HTTPException(
            status_code=503,
            detail="A recuperação de senha por e-mail não está disponível. Fale com o administrador do sistema.",
        )

    user = (await db.execute(
        select(Usuario).where(func.lower(Usuario.email) == data.email.strip().lower())
    )).scalar_one_or_none()

    if user and user.ativo:
        token = create_password_reset_token(user)
        link = f"{settings.FRONTEND_URL.rstrip('/')}/redefinir-senha?token={token}"
        html = email_service.render_system_email(
            "Redefinição de senha",
            [
                f"Olá, {user.nome}!",
                "Recebemos um pedido para redefinir a senha da sua conta. Clique no botão abaixo para criar uma nova senha.",
                f"O link vale por {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutos e só pode ser usado uma vez. "
                "Se você não fez esse pedido, ignore este e-mail: sua senha continua a mesma.",
            ],
            "Criar nova senha",
            link,
        )
        background.add_task(_enviar_email_sistema, user.email, f"Redefinição de senha - {settings.APP_NAME}", html)

    return {"message": "Se o e-mail estiver cadastrado, você receberá um link para redefinir a senha em instantes."}


@router.post("/redefinir-senha")
async def redefinir_senha(data: RedefinirSenhaRequest, db: AsyncSession = Depends(get_db)):
    """Define uma nova senha a partir do token recebido por e-mail."""
    invalido = HTTPException(status_code=400, detail="Link inválido ou expirado. Solicite uma nova redefinição de senha.")
    payload = decode_token(data.token)
    try:
        user_id = uuid.UUID(payload["sub"]) if payload else None
    except (KeyError, ValueError):
        user_id = None
    if not user_id:
        raise invalido

    user = await db.get(Usuario, user_id)
    if not user or not user.ativo or not password_reset_token_valid(payload, user):
        raise invalido

    _validar_nova_senha(data.senha)
    user.senha_hash = get_password_hash(data.senha)
    user.token_version = (user.token_version or 0) + 1  # encerra sessões abertas
    await db.commit()
    return {"message": "Senha redefinida com sucesso. Faça login com a nova senha."}


@router.post("/alterar-senha")
async def alterar_senha(
    data: AlterarSenhaRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Troca a senha do usuário logado. Encerra as outras sessões e devolve novos tokens."""
    if not verify_password(data.senha_atual, current_user.senha_hash):
        raise HTTPException(status_code=400, detail="A senha atual está incorreta.")
    _validar_nova_senha(data.nova_senha)
    current_user.senha_hash = get_password_hash(data.nova_senha)
    current_user.token_version = (current_user.token_version or 0) + 1
    await db.commit()
    return _issue_tokens(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Encerra todas as sessões do usuário (invalida access e refresh tokens emitidos)."""
    current_user.token_version = (current_user.token_version or 0) + 1
    await db.commit()


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Dados do usuário autenticado."""
    empresa = current_user.empresa
    plano_slug = (empresa.plano if empresa else None) or "gratuito"
    plano = await db.get(Plano, plano_slug)
    return UserInfo(
        id=str(current_user.id),
        nome=current_user.nome,
        email=current_user.email,
        cargo=current_user.cargo,
        role=current_user.role.value,
        empresa_id=str(current_user.empresa_id),
        empresa_nome=(empresa.nome_fantasia or empresa.razao_social) if empresa else None,
        empresa_cor_marca=empresa.cor_marca if empresa else None,
        empresa_plano=plano_slug,
        empresa_plano_nome=plano.nome if plano else plano_slug.capitalize(),
        is_superuser=current_user.is_superuser,
    )
