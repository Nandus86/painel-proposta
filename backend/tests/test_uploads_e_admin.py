import base64
import os

from sqlalchemy import update

from app.models.usuario import Usuario

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


async def test_upload_de_logo(client, conta):
    r = await conta.post("/api/empresas/logo", files={"file": ("logo.png", PNG_1PX, "image/png")})
    assert r.status_code == 200
    url = r.json()["logo_url"]
    r = await client.get(url)
    assert r.status_code == 200
    assert r.headers["x-content-type-options"] == "nosniff"
    os.remove(os.path.join("uploads", url.removeprefix("/uploads/")))


async def test_upload_recusa_svg_e_arquivo_disfarcado(conta):
    r = await conta.post("/api/empresas/logo", files={"file": ("x.svg", b"<svg onload=alert(1)/>", "image/svg+xml")})
    assert r.status_code == 400
    r = await conta.post("/api/empresas/logo", files={"file": ("x.png", b"<html>nao sou png</html>", "image/png")})
    assert r.status_code == 400


async def test_path_traversal_em_uploads(client):
    r = await client.get("/uploads/..%2f..%2fetc%2fpasswd")
    assert r.status_code in (403, 404)


async def test_rotas_de_superadmin_exigem_permissao(conta):
    for url in ["/api/superadmin/dashboard", "/api/empresas/admin/todas", "/api/admin/config", "/api/ai/openrouter/models"]:
        assert (await conta.get(url)).status_code == 403, url


async def test_superadmin_bloqueia_empresa(client, conta, nova_conta, db_session):
    admin = await nova_conta()
    await db_session.execute(update(Usuario).where(Usuario.email == admin.email).values(is_superuser=True))
    await db_session.commit()

    empresa_id = (await conta.get("/api/auth/me")).json()["empresa_id"]
    doc = await conta.criar_documento()

    r = await admin.post(f"/api/superadmin/empresas/{empresa_id}/acao", params={"acao": "bloquear"})
    assert r.status_code == 200

    assert (await conta.get("/api/auth/me")).status_code == 403
    r = await client.post("/api/auth/login", json={"email": conta.email, "senha": conta.senha})
    assert r.status_code == 403
    r = await client.get(f"/api/public/propostas/{doc['token_publico']}")
    assert r.status_code == 404


async def test_ia_sem_configuracao(conta):
    r = await conta.post("/api/ai/proposta/gerar-descricao", json={"titulo": "t", "cliente_nome": "c"})
    assert r.status_code == 503
    r = await conta.get("/api/ai/credits")
    assert r.status_code == 200 and r.json()["limit"] >= 0


async def test_dashboard(conta):
    await conta.criar_documento()
    for periodo in ["tudo", "hoje", "7dias", "30dias", "mes_atual", "ano_atual"]:
        r = await conta.get("/api/dashboard/metrics", params={"periodo": periodo})
        assert r.status_code == 200, periodo
    assert (await conta.get("/api/dashboard/activities")).status_code == 200
