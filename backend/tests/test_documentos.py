import pytest


@pytest.mark.parametrize("tipo", ["propostas", "orcamentos"])
async def test_criacao_calcula_valores_no_servidor(conta, tipo):
    cliente = await conta.criar_cliente()
    r = await conta.post(f"/api/{tipo}", json={
        "cliente_id": cliente["id"],
        "titulo": "Site institucional",
        "status": "aceita" if tipo == "propostas" else "aprovado",
        "items": [
            {"descricao": "Layout", "quantidade": 2, "preco_unitario": 100.5, "subtotal": 999999},
            {"descricao": "Hospedagem", "quantidade": 1, "preco_unitario": 50, "desconto": 10},
        ],
    })
    assert r.status_code == 201, r.text
    doc = r.json()
    assert float(doc["valor_total"]) == 241.0  # 2*100.5 + (50-10)
    assert doc["status"] == "rascunho"  # aceite não pode ser definido na criação
    assert doc["numero"] == 1
    assert doc["validade_dias"] == 30  # padrão da empresa


async def test_numeracao_sequencial_por_empresa(conta, nova_conta):
    p1 = await conta.criar_documento()
    p2 = await conta.criar_documento()
    outra = await nova_conta()
    p_outra = await outra.criar_documento()
    assert (p1["numero"], p2["numero"], p_outra["numero"]) == (1, 2, 1)


async def test_cota_do_plano_gratuito(conta):
    cliente = await conta.criar_cliente()
    for _ in range(3):
        await conta.criar_documento(cliente_id=cliente["id"])
    r = await conta.post("/api/propostas", json={
        "cliente_id": cliente["id"], "titulo": "Excedente", "items": [{"descricao": "x", "preco_unitario": 1}],
    })
    assert r.status_code == 402


async def test_documento_sem_itens_e_recusado(conta):
    cliente = await conta.criar_cliente()
    r = await conta.post("/api/propostas", json={"cliente_id": cliente["id"], "titulo": "Vazia", "items": []})
    assert r.status_code == 400


async def test_busca_por_titulo_e_por_cliente(conta):
    cliente = await conta.criar_cliente(razao_social="Padaria Pão Quente")
    await conta.criar_documento(cliente_id=cliente["id"], titulo="Cardápio digital")
    await conta.criar_documento(titulo="Outro projeto")

    r = await conta.get("/api/propostas", params={"search": "padaria"})
    assert r.json()["total"] == 1
    r = await conta.get("/api/propostas", params={"search": "cardápio"})
    assert r.json()["total"] == 1


async def test_atualizacao_recalcula_total_e_validade(conta):
    doc = await conta.criar_documento()
    r = await conta.put(f"/api/propostas/{doc['id']}", json={
        "validade_dias": 10,
        "items": [{"descricao": "Novo item", "quantidade": 3, "preco_unitario": 10}],
    })
    assert r.status_code == 200
    atualizado = r.json()
    assert float(atualizado["valor_total"]) == 30.0
    assert atualizado["validade_dias"] == 10
    assert len(atualizado["items"]) == 1


async def test_pdf_e_preview(conta):
    cliente = await conta.criar_cliente()
    doc = await conta.criar_documento(cliente_id=cliente["id"], observacoes="## Escopo\n\n**Texto** <script>alert(1)</script>")

    r = await conta.get(f"/api/propostas/{doc['id']}/pdf")
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"

    r = await conta.get(f"/api/orcamentos/{(await conta.criar_documento('orcamentos'))['id']}/pdf")
    assert r.content[:4] == b"%PDF"

    total_antes = (await conta.get("/api/propostas")).json()["total"]
    r = await conta.post("/api/propostas/preview", json={
        "cliente_id": cliente["id"], "titulo": "Preview", "items": [{"descricao": "x", "preco_unitario": 1}],
    })
    assert r.status_code == 200 and r.content[:4] == b"%PDF"
    assert (await conta.get("/api/propostas")).json()["total"] == total_antes  # preview não persiste


async def test_envio_de_email_sem_smtp_da_empresa(conta):
    doc = await conta.criar_documento()
    r = await conta.post(f"/api/propostas/{doc['id']}/enviar-email")
    assert r.status_code == 400
    assert "SMTP" in r.json()["detail"]


async def test_exclusao(conta):
    doc = await conta.criar_documento()
    assert (await conta.delete(f"/api/propostas/{doc['id']}")).status_code == 200
    assert (await conta.get(f"/api/propostas/{doc['id']}")).status_code == 404


async def test_cliente_com_documentos_nao_pode_ser_excluido(conta):
    cliente = await conta.criar_cliente()
    await conta.criar_documento(cliente_id=cliente["id"])
    r = await conta.delete(f"/api/clientes/{cliente['id']}")
    assert r.status_code == 409
