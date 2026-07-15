import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT u.email, e.smtp_user, e.smtp_password 
            FROM usuarios u 
            JOIN empresas e ON u.empresa_id = e.id 
            WHERE u.email = 'fernandomskt86@gmail.com'
        """))
        row = result.fetchone()
        if row:
            print('User:', row[0])
            print('SMTP User:', row[1])
            print('SMTP Pass is set:', bool(row[2]))
        else:
            print("User not found")

asyncio.run(check())
