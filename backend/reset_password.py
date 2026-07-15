import asyncio
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.usuario import Usuario
from app.core.security import get_password_hash

async def reset_password():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Usuario).where(Usuario.email == 'teste@teste.com'))
        admin = result.scalar_one_or_none()
        
        if not admin:
            print('User not found')
            return
        
        new_hash = get_password_hash('admin123')
        admin.senha_hash = new_hash
        await session.commit()
        print(f'Password reset for {admin.email}')
        
        # Verify
        from app.core.security import verify_password
        print(f'verify: {verify_password("admin123", new_hash)}')

asyncio.run(reset_password())
