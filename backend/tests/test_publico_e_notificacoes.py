from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app.models.proposta import Proposta


async def _notificacoes(conta):
    r = await conta.get("/api/notificacoes")
    assert r.status_code == 200
    return r.json()


async def test_primeira_visualizacao_gera_uma_notificacao(client, conta):
    doc = await conta.criar_documento()
    for _ in range(3):
        r = await client.get(f"/api/public/propostas/{doc['token_publico']}")
        assert r.status_code == 200

    dados = await _notificacoes(conta)
    visualizadas = [n for n in dados["items"] if n["tipo"] == "visualizada"]
    assert len(visualizadas) == 1
    assert visualizadas[0]["link"] == f"/propostas/{doc['id']}/edit"

    lista = (await conta.get("/api/propostas")).json()["items"]
    assert [d for d in lista if d["id"] == doc["id"]][0]["visualizacoes"] == 3


async def test_pagina_publica_nao_expoe_cnpj_provisorio(client, conta):
    doc = await conta.criar_documento()
    r = await client.get(f"/api/public/propostas/{doc['token_publico']}")
    assert r.json()["empresa"]["cnpj"] is None


async def test_aceite_notifica_e_envia_email_ao_vendedor(client, conta, emails):
    doc = await conta.criar_documento()
    r = await client.post(f"/api/public/propostas/{doc['token_publico']}/aceitar", json={"aceite": True})
    assert r.status_code == 200

    dados = await _notificacoes(conta)
    assert any(n["tipo"] == "aceita" for n in dados["items"])
    assert any(e["to_email"] == conta.email and "aceita" in e["subject"] for e in emails)

    r = await client.post(f"/api/public/propostas/{doc['token_publico']}/aceitar", json={"aceite": True})
    assert r.status_code == 400  # não aceita duas vezes


async def test_aprovacao_de_orcamento(client, conta):
    doc = await conta.criar_documento("orcamentos")
    r = await client.post(f"/api/public/orcamentos/{doc['token_publico']}/aceitar", json={"aceite": True})
    assert r.status_code == 200
    r = await client.get(f"/api/public/orcamentos/{doc['token_publico']}")
    assert r.json()["status"] == "aprovado"


async def test_documento_vencido_nao_pode_ser_aceito(client, conta, db_session):
    doc = await conta.criar_documento()
    await db_session.execute(
        update(Proposta).where(Proposta.id == doc["id"]).values(data_validade=datetime.now(timezone.utc) - timedelta(days=1))
    )
    await db_session.commit()

    r = await client.get(f"/api/public/propostas/{doc['token_publico']}")
    assert r.json()["expirado"] is True
    r = await client.post(f"/api/public/propostas/{doc['token_publico']}/aceitar", json={"aceite": True})
    assert r.status_code == 400


async def test_marcar_notificacoes_como_lidas(client, conta, nova_conta):
    doc = await conta.criar_documento()
    await client.get(f"/api/public/propostas/{doc['token_publico']}")
    dados = await _notificacoes(conta)
    assert dados["nao_lidas"] >= 1

    outro = await nova_conta()
    alvo = dados["items"][0]["id"]
    assert (await outro.post(f"/api/notificacoes/{alvo}/lida")).status_code == 404  # não mexe na de outro usuário

    assert (await conta.post(f"/api/notificacoes/{alvo}/lida")).status_code == 200
    assert (await conta.post("/api/notificacoes/lidas")).status_code == 200
    assert (await _notificacoes(conta))["nao_lidas"] == 0


async def test_link_invalido(client):
    r = await client.get("/api/public/propostas/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
