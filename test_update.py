import sys
sys.path.append('.')

import asyncio
from app.core.security import create_access_token
from app.database import async_session
from sqlalchemy import select
from app.models.usuario import Usuario

async def main():
    async with async_session() as db:
        # Get first user
        result = await db.execute(select(Usuario))
        user = result.scalars().first()
        if not user:
            print("No user")
            return
            
        token = create_access_token({"sub": str(user.id)})
        
        # Now use requests
        import requests
        headers = {'Authorization': f'Bearer {token}'}
        res_get = requests.get('http://localhost:8000/api/orcamentos?limit=1', headers=headers)
        items = res_get.json().get('items', [])
        if not items:
            print("No orcamentos")
            return
            
        orcamento = requests.get(f'http://localhost:8000/api/orcamentos/{items[0]["id"]}', headers=headers).json()
        res_put = requests.put(f'http://localhost:8000/api/orcamentos/{items[0]["id"]}', json=orcamento, headers=headers)
        print("PUT:", res_put.status_code)
        print(res_put.json())

if __name__ == "__main__":
    asyncio.run(main())
