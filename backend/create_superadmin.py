import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal
from app.core.security import get_password_hash
import uuid
from datetime import datetime, timezone

async def create_or_update_superadmin():
    async with AsyncSessionLocal() as session:
        # Check if user exists
        result = await session.execute(text("SELECT id FROM usuarios WHERE email = 'superadmin@teste.com'"))
        user_id = result.scalar_one_or_none()
        
        senha_hash = get_password_hash('teste123')
        now = datetime.now(timezone.utc)
        
        if user_id:
            await session.execute(
                text("UPDATE usuarios SET is_superuser = true, senha_hash = :senha WHERE id = :id"),
                {"senha": senha_hash, "id": user_id}
            )
            print("Usuário existente foi atualizado para Superadmin.")
        else:
            # Create dummy empresa
            empresa_id = str(uuid.uuid4())
            await session.execute(
                text("INSERT INTO empresas (id, razao_social, cnpj, created_at, updated_at, whatsapp_conectado, telegram_conectado, pagamento_modo_teste, prefixo_proposta, validade_padrao_dias, ai_credits_used_today, ai_credits_limit) VALUES (:id, 'Empresa Admin (Sistema)', :cnpj, :now, :now, false, false, true, 'PROP', 30, 0, 20)"),
                {"id": empresa_id, "cnpj": f"ADM-{str(uuid.uuid4())[:14]}", "now": now}
            )
            
            # Create user
            user_id = str(uuid.uuid4())
            await session.execute(
                text("INSERT INTO usuarios (id, empresa_id, nome, email, senha_hash, role, cargo, is_superuser, ativo, created_at, updated_at) VALUES (:id, :empresa_id, 'Super Admin', 'superadmin@teste.com', :senha, 'ADMIN', 'Super Administrador', true, true, :now, :now)"),
                {"id": user_id, "empresa_id": empresa_id, "senha": senha_hash, "now": now}
            )
            print("Novo usuário Superadmin criado com sucesso!")
            
        await session.commit()

if __name__ == "__main__":
    asyncio.run(create_or_update_superadmin())
