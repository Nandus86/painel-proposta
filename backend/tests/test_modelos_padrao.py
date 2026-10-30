import uuid
import pytest
from sqlalchemy import select

from app.models.empresa import Empresa
from app.models.modelo_proposta import ModeloProposta
from app.services.modelos_padrao import MODELOS_PADRAO, seed_modelos_padrao


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
