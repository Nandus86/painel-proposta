"""Isolamento entre empresas (multi-tenant)."""


async def test_nao_usa_cliente_de_outra_empresa(conta, nova_conta):
    invasor = await nova_conta()
    cliente_alheio = await conta.criar_cliente()
    r = await invasor.post("/api/propostas", json={
        "cliente_id": cliente_alheio["id"], "titulo": "x", "items": [{"descricao": "x", "preco_unitario": 1}],
    })
    assert r.status_code == 404


async def test_nao_usa_servico_de_outra_empresa(conta, nova_conta):
    invasor = await nova_conta()
    servico_alheio = await conta.criar_servico()
    cliente = await invasor.criar_cliente()
    r = await invasor.post("/api/propostas", json={
        "cliente_id": cliente["id"], "titulo": "x",
        "items": [{"descricao": "x", "preco_unitario": 1, "servico_id": servico_alheio["id"]}],
    })
    assert r.status_code == 404


async def test_nao_le_nem_altera_documento_de_outra_empresa(conta, nova_conta):
    invasor = await nova_conta()
    doc = await conta.criar_documento()
    assert (await invasor.get(f"/api/propostas/{doc['id']}")).status_code == 404
    assert (await invasor.put(f"/api/propostas/{doc['id']}", json={"titulo": "hack"})).status_code == 404
    assert (await invasor.delete(f"/api/propostas/{doc['id']}")).status_code == 404
    assert (await invasor.get(f"/api/propostas/{doc['id']}/pdf")).status_code == 404
    assert (await invasor.get("/api/propostas")).json()["total"] == 0


async def test_empresa_nao_ve_segredos(conta):
    r = await conta.put("/api/empresas/me", json={"stripe_secret_key": "sk_test_123", "smtp_password": "segredo"})
    assert r.status_code == 200
    dados = r.json()
    assert "stripe_secret_key" not in dados and "smtp_password" not in dados
    assert dados["has_stripe_secret_key"] and dados["has_smtp_password"]


async def test_logo_externa_e_ignorada(conta):
    r = await conta.put("/api/empresas/me", json={"logo_url": "http://169.254.169.254/latest/meta-data"})
    assert r.json()["logo_url"] is None


async def test_cnpj_valido_e_unico(conta, nova_conta):
    r = await conta.put("/api/empresas/me", json={"cnpj": "123"})
    assert r.status_code == 422
    r = await conta.put("/api/empresas/me", json={"cnpj": "45.723.174/0001-10"})
    assert r.json()["cnpj"] == "45.723.174/0001-10"
    outra = await nova_conta()
    r = await outra.put("/api/empresas/me", json={"cnpj": "45723174000110"})
    assert r.status_code == 400
