import asyncio
import sys
from app.database import AsyncSessionLocal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.proposta import Proposta
from app.services.pdf import generate_proposal_pdf

async def main():
    async with AsyncSessionLocal() as db:
        # Pega a última proposta
        stmt = select(Proposta).options(
            selectinload(Proposta.items),
            selectinload(Proposta.cliente),
            selectinload(Proposta.empresa),
            selectinload(Proposta.usuario)
        ).order_by(Proposta.id.desc()).limit(1)
        result = await db.execute(stmt)
        proposta = result.scalar_one_or_none()
        
        if not proposta:
            print("Nenhuma proposta encontrada.")
            return

        print(f"Gerando PDF para a proposta {proposta.numero}...")
        try:
            pdf_bytes = generate_proposal_pdf(proposta)
            print("PDF gerado com sucesso!")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
