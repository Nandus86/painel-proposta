from app.schemas.proposta import PropostaCreate

payload = {
  "numero": "",
  "titulo": "Test",
  "cliente_id": "00000000-0000-0000-0000-000000000000",
  "status": "rascunho",
  "validade_dias": 15,
  "condicoes_pagamento": "50% entrada",
  "observacoes": "obs",
  "valor_total": 0,
  "items": [{
      "servico_id": None,
      "descricao": "Item 1",
      "quantidade": 1,
      "preco_unitario": 0,
      "subtotal": 0,
      "ordem": 0
  }]
}

try:
    p = PropostaCreate(**payload)
    print("Parsed OK")
except Exception as e:
    print(e)
