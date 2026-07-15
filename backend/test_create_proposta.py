import asyncio
import sys
from app.database import AsyncSessionLocal
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.schemas.proposta import PropostaCreate, ItemPropostaCreate
from app.routers.propostas import create_proposta

async def main():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        cliente = (await db.execute(select(Cliente).limit(1))).scalar_one_or_none()
        usuario = (await db.execute(select(Usuario).limit(1))).scalar_one_or_none()
        if not cliente or not usuario:
            print("Sem cliente ou usuario")
            return
            
        proposta_in = PropostaCreate(
            cliente_id=cliente.id,
            titulo="Proposta Teste",
            items=[ItemPropostaCreate(descricao="Item 1", preco_unitario=10.0, subtotal=10.0)]
        )
        try:
            res = await create_proposta(db=db, proposta_in=proposta_in, current_user=usuario)
            print("Criado com sucesso:", res)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
