"""Infraestrutura dos testes: banco Postgres real (schema recriado via Alembic) + cliente HTTP ASGI.

Banco usado: TEST_DATABASE_URL (padrão: postgres local, banco `painel_proposta_test`).
ATENÇÃO: o schema `public` desse banco é APAGADO no início da sessão de testes.
"""
import os
import uuid

TEST_DB = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/painel_proposta_test"
)
os.environ.update({
    "ENVIRONMENT": "test",
    "JOBS_ENABLED": "false",
    "SECRET_KEY": "test-secret-key-0123456789abcdef0123456789",
    "DATABASE_URL": TEST_DB,
    "DATABASE_URL_SYNC": TEST_DB.replace("+asyncpg", "+psycopg"),
    "FRONTEND_URL": "https://app.teste.com",
    "SMTP_HOST": "",
    # Variáveis de ambiente têm prioridade sobre o backend/.env local: isola os testes dele
    "OPENAI_API_KEY": "",
    "ANTHROPIC_API_KEY": "",
    "LLM_PROVIDER": "openai",
    "STORAGE_PROVIDER": "local",
    "MINIO_ENDPOINT": "",
    "PUBLIC_LINKS_USE_TENANT_DOMAIN": "false",
})

import httpx  # noqa: E402
import psycopg  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from pytest_asyncio import is_async_test  # noqa: E402

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pytest_collection_modifyitems(items):
    # Todos os testes compartilham o event loop da sessão (o pool do SQLAlchemy fica preso a ele)
    marker = pytest.mark.asyncio(loop_scope="session")
    for item in items:
        if is_async_test(item):
            item.add_marker(marker, append=False)


@pytest.fixture(scope="session", autouse=True)
def database():
    """Recria o schema do zero e aplica todas as migrações (também valida as migrações)."""
    dsn = os.environ["DATABASE_URL_SYNC"].replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
        conn.execute("CREATE SCHEMA public")
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(scope="session")
async def client(database):
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=60) as c:
        yield c


@pytest.fixture
def emails(monkeypatch):
    """Ativa o SMTP do sistema e captura os e-mails enviados (nada sai para a rede)."""
    from app.config import settings
    from app.services import email as email_service

    enviados = []

    def fake_send(**kwargs):
        enviados.append(kwargs)

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.teste.com")
    monkeypatch.setattr(settings, "SMTP_USER", "naoresponda@teste.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "x")
    monkeypatch.setattr(email_service, "_smtp_send", fake_send)
    return enviados


class Conta:
    """Empresa + usuário admin criados via API, com helpers para chamadas autenticadas."""

    def __init__(self, client: httpx.AsyncClient, email: str, senha: str, tokens: dict):
        self.client = client
        self.email = email
        self.senha = senha
        self.access = tokens["access_token"]
        self.refresh = tokens["refresh_token"]

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.access}"}

    async def get(self, url, **kw):
        return await self.client.get(url, headers=self.headers, **kw)

    async def post(self, url, **kw):
        return await self.client.post(url, headers=self.headers, **kw)

    async def put(self, url, **kw):
        return await self.client.put(url, headers=self.headers, **kw)

    async def delete(self, url, **kw):
        return await self.client.delete(url, headers=self.headers, **kw)

    async def criar_cliente(self, **dados):
        payload = {"razao_social": f"Cliente {uuid.uuid4().hex[:6]}", "email": "cliente@exemplo.com", **dados}
        r = await self.post("/api/clientes", json=payload)
        assert r.status_code in (200, 201), r.text
        return r.json()

    async def criar_servico(self, **dados):
        r = await self.post("/api/servicos", json={"nome": "Consultoria", "preco": 100, **dados})
        assert r.status_code in (200, 201), r.text
        return r.json()

    async def criar_documento(self, tipo="propostas", cliente_id=None, **dados):
        if cliente_id is None:
            cliente_id = (await self.criar_cliente())["id"]
        payload = {
            "cliente_id": cliente_id,
            "titulo": "Projeto de teste",
            "items": [{"descricao": "Serviço", "quantidade": 2, "preco_unitario": 150}],
            **dados,
        }
        r = await self.post(f"/api/{tipo}", json=payload)
        assert r.status_code == 201, r.text
        return r.json()


@pytest.fixture
def nova_conta(client):
    async def _criar(senha="senhaforte123", empresa="Empresa Teste"):
        email = f"user-{uuid.uuid4().hex[:10]}@teste.com"
        r = await client.post("/api/auth/register", json={"nome": "Ana Teste", "email": email, "senha": senha, "empresa": empresa})
        assert r.status_code == 201, r.text
        return Conta(client, email, senha, r.json())

    return _criar


@pytest.fixture
async def conta(nova_conta):
    return await nova_conta()


@pytest.fixture
async def db_session():
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session
