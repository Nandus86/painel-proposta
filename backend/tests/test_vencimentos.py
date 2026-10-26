from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app.models.orcamento import Orcamento, StatusOrcamento
from app.models.proposta import Proposta, StatusProposta
from app.services.notificacoes import processar_vencimentos


async def _ajustar(db, Model, doc_id, **valores):
    await db.execute(update(Model).where(Model.id == doc_id).values(**valores))
    await db.commit()


async def test_documento_enviado_vence_e_avisa_o_vendedor(conta, db_session):
    agora = datetime.now(timezone.utc)
    proposta = await conta.criar_documento()
    orcamento = await conta.criar_documento("orcamentos")
    rascunho = await conta.criar_documento()

    await _ajustar(db_session, Proposta, proposta["id"], status=StatusProposta.ENVIADA, data_validade=agora - timedelta(hours=1))
    await _ajustar(db_session, Orcamento, orcamento["id"], status=StatusOrcamento.ENVIADO, data_validade=agora - timedelta(hours=1))
    await _ajustar(db_session, Proposta, rascunho["id"], data_validade=agora - timedelta(hours=1))

    resumo = await processar_vencimentos(db_session)
    assert resumo["executada"] and resumo["vencidos"] >= 2

    assert (await conta.get(f"/api/propostas/{proposta['id']}")).json()["status"] == "expirada"
    assert (await conta.get(f"/api/orcamentos/{orcamento['id']}")).json()["status"] == "vencido"
    # rascunhos não são marcados como vencidos
    assert (await conta.get(f"/api/propostas/{rascunho['id']}")).json()["status"] == "rascunho"

    notifs = (await conta.get("/api/notificacoes")).json()["items"]
    assert len([n for n in notifs if n["tipo"] == "vencida"]) == 2

    # idempotente: rodar de novo não duplica avisos
    await processar_vencimentos(db_session)
    notifs = (await conta.get("/api/notificacoes")).json()["items"]
    assert len([n for n in notifs if n["tipo"] == "vencida"]) == 2


async def test_aviso_de_vencimento_proximo_uma_unica_vez(conta, db_session):
    doc = await conta.criar_documento()
    await _ajustar(db_session, Proposta, doc["id"], status=StatusProposta.ENVIADA,
                   data_validade=datetime.now(timezone.utc) + timedelta(days=2))

    await processar_vencimentos(db_session)
    await processar_vencimentos(db_session)

    notifs = (await conta.get("/api/notificacoes")).json()["items"]
    vencendo = [n for n in notifs if n["tipo"] == "vencendo"]
    assert len(vencendo) == 1
    assert "vence" in vencendo[0]["titulo"]


async def test_prorrogar_validade_reabre_documento_vencido(conta, db_session):
    doc = await conta.criar_documento()
    await _ajustar(db_session, Proposta, doc["id"], status=StatusProposta.EXPIRADA,
                   data_validade=datetime.now(timezone.utc) - timedelta(days=1))

    r = await conta.put(f"/api/propostas/{doc['id']}", json={"validade_dias": 15})
    assert r.status_code == 200
    assert r.json()["status"] == "enviada"
