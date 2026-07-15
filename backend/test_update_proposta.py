import asyncio
import sys
from app.database import AsyncSessionLocal
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.schemas.proposta import PropostaUpdate, ItemPropostaCreate, PropostaResponse
from app.routers.propostas import update_proposta, create_proposta, PropostaCreate

async def main():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        cliente = (await db.execute(select(Cliente).limit(1))).scalar_one_or_none()
        usuario = (await db.execute(select(Usuario).limit(1))).scalar_one_or_none()
        
        proposta_in = PropostaCreate(
            cliente_id=cliente.id,
            titulo="Proposta Teste Update",
            items=[ItemPropostaCreate(descricao="Item 1", preco_unitario=10.0, subtotal=10.0)]
        )
        proposta = await create_proposta(db=db, proposta_in=proposta_in, current_user=usuario)
        
        # Test Response validation for create
        try:
            resp = PropostaResponse.model_validate(proposta)
            print("Create Response OK")
        except Exception as e:
            print("Create Response Failed:", e)

        update_in = PropostaUpdate(
            titulo="Proposta Atualizada",
            items=[ItemPropostaCreate(descricao="Item 2", preco_unitario=20.0, subtotal=20.0)]
        )
        proposta_updated = await update_proposta(db=db, id=proposta.id, proposta_in=update_in, current_user=usuario)
        
        # Test Response validation for update
        try:
            resp2 = PropostaResponse.model_validate(proposta_updated)
            print("Update Response OK")
        except Exception as e:
            print("Update Response Failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
