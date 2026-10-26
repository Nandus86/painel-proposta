import re


def _token_do_email(enviado: dict) -> str:
    m = re.search(r"/redefinir-senha\?token=([\w\-.]+)", enviado["html_content"])
    assert m, "link de redefinição não encontrado no e-mail"
    return m.group(1)


async def test_sem_smtp_do_sistema_retorna_503(client, conta):
    r = await client.post("/api/auth/esqueci-senha", json={"email": conta.email})
    assert r.status_code == 503


async def test_fluxo_completo_de_redefinicao(client, conta, emails):
    r = await client.post("/api/auth/esqueci-senha", json={"email": conta.email.upper()})
    assert r.status_code == 200
    assert len(emails) == 1
    assert emails[0]["to_email"] == conta.email
    assert "https://app.teste.com/redefinir-senha?token=" in emails[0]["html_content"]
    token = _token_do_email(emails[0])

    r = await client.post("/api/auth/redefinir-senha", json={"token": token, "senha": "curta"})
    assert r.status_code == 400

    r = await client.post("/api/auth/redefinir-senha", json={"token": token, "senha": "senhanova123"})
    assert r.status_code == 200

    # uso único: o mesmo link não funciona de novo
    r = await client.post("/api/auth/redefinir-senha", json={"token": token, "senha": "outrasenha123"})
    assert r.status_code == 400

    # sessões antigas encerradas; login com a senha nova
    assert (await conta.get("/api/auth/me")).status_code == 401
    r = await client.post("/api/auth/login", json={"email": conta.email, "senha": "senhanova123"})
    assert r.status_code == 200


async def test_email_inexistente_tem_a_mesma_resposta(client, emails):
    r = await client.post("/api/auth/esqueci-senha", json={"email": "ninguem@teste.com"})
    assert r.status_code == 200
    assert emails == []


async def test_tokens_invalidos(client, conta):
    for token in ["abc", conta.access, conta.refresh]:
        r = await client.post("/api/auth/redefinir-senha", json={"token": token, "senha": "senhanova123"})
        assert r.status_code == 400, token


async def test_cadastro_envia_boas_vindas(client, emails):
    r = await client.post("/api/auth/register", json={"nome": "Bia", "email": "bia-boasvindas@teste.com", "senha": "senhaforte123"})
    assert r.status_code == 201
    assert len(emails) == 1
    assert "Bem-vindo" in emails[0]["subject"]
