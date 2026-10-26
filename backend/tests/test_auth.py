async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_cadastro_recusa_senha_curta(client):
    r = await client.post("/api/auth/register", json={"nome": "X", "email": "curta@teste.com", "senha": "1234567"})
    assert r.status_code == 400


async def test_cadastro_cria_empresa_com_nome_informado(conta):
    me = (await conta.get("/api/auth/me")).json()
    assert me["empresa_nome"] == "Empresa Teste"
    assert me["role"] == "admin"
    assert me["empresa_plano"] == "gratuito"


async def test_email_duplicado_e_case_insensitive(client, conta):
    r = await client.post("/api/auth/register", json={"nome": "Y", "email": conta.email.upper(), "senha": "senhaforte123"})
    assert r.status_code == 400
    r = await client.post("/api/auth/login", json={"email": conta.email.upper(), "senha": conta.senha})
    assert r.status_code == 200


async def test_login_senha_errada(client, conta):
    r = await client.post("/api/auth/login", json={"email": conta.email, "senha": "errada123"})
    assert r.status_code == 401


async def test_rota_protegida_sem_token(client):
    r = await client.get("/api/propostas")
    assert r.status_code in (401, 403)


async def test_refresh_e_logout_revogam_tokens(client, conta):
    r = await client.post("/api/auth/refresh", json={"refresh_token": conta.refresh})
    assert r.status_code == 200

    r = await conta.post("/api/auth/logout")
    assert r.status_code == 204

    assert (await conta.get("/api/auth/me")).status_code == 401
    r = await client.post("/api/auth/refresh", json={"refresh_token": conta.refresh})
    assert r.status_code == 401


async def test_refresh_nao_aceita_access_token(client, conta):
    r = await client.post("/api/auth/refresh", json={"refresh_token": conta.access})
    assert r.status_code == 401


async def test_alterar_senha(client, conta):
    r = await conta.post("/api/auth/alterar-senha", json={"senha_atual": "errada123", "nova_senha": "novasenha123"})
    assert r.status_code == 400

    r = await conta.post("/api/auth/alterar-senha", json={"senha_atual": conta.senha, "nova_senha": "novasenha123"})
    assert r.status_code == 200
    novos = r.json()

    # sessão antiga encerrada, a nova continua válida
    assert (await conta.get("/api/auth/me")).status_code == 401
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {novos['access_token']}"})
    assert r.status_code == 200

    r = await client.post("/api/auth/login", json={"email": conta.email, "senha": "novasenha123"})
    assert r.status_code == 200
