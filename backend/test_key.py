import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.config import settings
from app.models.sistema_config import SistemaConfig
from app.core.security import decrypt_data

async def check():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(SistemaConfig).where(SistemaConfig.id == 1))
        config = result.scalar_one_or_none()
        if config:
            print(f"Encrypted Key: {config.openrouter_key}")
            decrypted = decrypt_data(config.openrouter_key)
            print(f"Decrypted Key: '{decrypted}'")
        else:
            print("No config found")
            
asyncio.run(check())
