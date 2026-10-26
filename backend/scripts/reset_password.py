"""Redefine a senha de um usuário e encerra todas as sessões dele.

Uso (dentro do container):
    docker compose exec backend python -m scripts.reset_password --email usuario@empresa.com
"""
import argparse
import asyncio
import getpass
import os
import sys

from sqlalchemy import select

from app.core.security import get_password_hash
from app.database import AsyncSessionLocal
from app.models.usuario import Usuario


async def main(email: str) -> None:
    senha = os.environ.get("NEW_PASSWORD") or getpass.getpass("Nova senha: ")
    if len(senha) < 8:
        sys.exit("A senha deve ter pelo menos 8 caracteres.")

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(Usuario).where(Usuario.email == email))).scalar_one_or_none()
        if not user:
            sys.exit(f"Usuário {email} não encontrado.")
        user.senha_hash = get_password_hash(senha)
        user.token_version = (user.token_version or 0) + 1
        await session.commit()
        print(f"Senha de {email} redefinida.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    asyncio.run(main(args.email.strip().lower()))
