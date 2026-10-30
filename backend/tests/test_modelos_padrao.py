import json
import uuid
import pytest
from sqlalchemy import select

from app.models.empresa import Empresa
from app.models.modelo_proposta import ModeloProposta
from app.services.modelos_padrao import MODELOS_PADRAO, seed_modelos_padrao
from app.routers.ai import _parse_modelo_json


def test_modelos_padrao_definicao():
    """Valida se existem os 3 tipos exigidos com seus devidos campos e tags."""
    assert len(MODELOS_PADRAO) == 3
    titulos = [m["titulo"].lower() for m in MODELOS_PADRAO]

    assert any("serviço" in t or "servico" in t for t in titulos)
    assert any("produto" in t for t in titulos)
    assert any("comercial" in t or "parceria" in t for t in titulos)

    for m in MODELOS_PADRAO:
        conteudo = m["conteudo"]
        assert "{{cliente}}" in conteudo
        assert "{{itens}}" in conteudo
        assert "{{valor_total}}" in conteudo
        assert "{{condicoes_pagamento}}" in conteudo


@pytest.mark.asyncio
async def test_seed_modelos_padrao_idempotente(db_session):
    """Garante que seed cria 3 modelos e não duplica se chamado novamente."""
    empresa = Empresa(
        razao_social="Empresa Teste Seed",
        cnpj=f"TMP-{uuid.uuid4().hex[:14]}",
    )
    db_session.add(empresa)
    await db_session.flush()

    # Inicialmente vazio
    result = await db_session.execute(
        select(ModeloProposta).where(ModeloProposta.empresa_id == empresa.id)
    )
    assert len(result.scalars().all()) == 0

    # 1ª execução: cria 3
    criados = await seed_modelos_padrao(db_session, empresa.id)
    assert len(criados) == 3

    # 2ª execução: retorna os mesmos 3 sem duplicar
    repetidos = await seed_modelos_padrao(db_session, empresa.id)
    assert len(repetidos) == 3
    assert {m.id for m in criados} == {m.id for m in repetidos}


@pytest.mark.asyncio
async def test_api_list_modelos_auto_seed(conta):
    """Ao listar modelos de uma conta nova, os 3 modelos padrão estão disponíveis."""
    resp = await conta.get("/api/modelos")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    titulos = [m["titulo"].lower() for m in data]
    assert any("serviço" in t or "servico" in t for t in titulos)
    assert any("produto" in t for t in titulos)
    assert any("comercial" in t or "parceria" in t for t in titulos)


def test_parse_modelo_json():
    """Testa extração de JSON gerado pelo LLM em múltiplos formatos."""
    # Formato com markdown fences
    md_json = '```json\n{"titulo": "Proposta Solar", "conteudo": "# Solar\\n{{itens}}"}\n```'
    p1 = _parse_modelo_json(md_json)
    assert p1["titulo"] == "Proposta Solar"
    assert "{{itens}}" in p1["conteudo"]

    # Formato JSON puro
    raw_json = '{"titulo": "Proposta Manutenção", "conteudo": "{{cliente}}"}'
    p2 = _parse_modelo_json(raw_json)
    assert p2["titulo"] == "Proposta Manutenção"

    # Fallback para texto plano
    plain = "# Proposta Especial de Consultoria\nTexto simples com {{valor_total}}"
    p3 = _parse_modelo_json(plain)
    assert p3["titulo"] == "Proposta Especial de Consultoria"
    assert "{{valor_total}}" in p3["conteudo"]


@pytest.mark.asyncio
async def test_api_gerar_modelo_ia_validacao(conta):
    """Valida erro se o briefing for enviado vazio."""
    resp = await conta.post("/api/ai/modelo/gerar", json={"instrucoes": "   "})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_api_gerar_modelo_ia_sucesso(conta, monkeypatch):
    """Testa geração de modelo via IA e consumo do crédito diário."""
    from app.routers import ai as ai_router

    class FakeResponse:
        content = json.dumps({
            "titulo": "Proposta de TI Gerada por IA",
            "conteudo": "# Proposta TI\n\n**Cliente:** {{cliente}}\n\n{{itens}}\n\n**Total:** R$ {{valor_total}}"
        })

    class FakeLLM:
        async def ainvoke(self, messages):
            return FakeResponse()

    monkeypatch.setattr(ai_router, "llm_disponivel", lambda: True)
    monkeypatch.setattr(ai_router, "get_llm", lambda *a, **k: FakeLLM())

    resp = await conta.post("/api/ai/modelo/gerar", json={
        "instrucoes": "Crie um modelo para serviços de TI e suporte de servidores.",
        "tom": "Formal e Técnico",
        "tipo": "Serviço"
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["titulo"] == "Proposta de TI Gerada por IA"
    assert "{{cliente}}" in data["conteudo"]
    assert "{{itens}}" in data["conteudo"]
    assert "{{valor_total}}" in data["conteudo"]
    assert "creditos_restantes" in data
