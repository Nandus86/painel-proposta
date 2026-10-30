"""Cria (ou promove) um usuário super administrador do sistema.

Uso (dentro do container):
    docker compose exec backend python -m scripts.create_superadmin --email voce@empresa.com --nome "Seu Nome"

A senha é pedida de forma interativa (ou via variável SUPERADMIN_PASSWORD).
"""
import argparse
import asyncio
import getpass
import os
import sys
import uuid

from sqlalchemy import select

from app.core.security import get_password_hash
from app.database import AsyncSessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario, UserRole
from app.services.modelos_padrao import seed_modelos_padrao


def _read_password() -> str:
    senha = os.environ.get("SUPERADMIN_PASSWORD")
    if senha:
        return senha
    senha = getpass.getpass("Senha do superadmin: ")
    if senha != getpass.getpass("Confirme a senha: "):
        sys.exit("As senhas não conferem.")
    return senha


async def main(email: str, nome: str) -> None:
    senha = _read_password()
    if len(senha) < 8:
        sys.exit("A senha deve ter pelo menos 8 caracteres.")

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(Usuario).where(Usuario.email == email))).scalar_one_or_none()

        if user:
            user.is_superuser = True
            user.ativo = True
            user.senha_hash = get_password_hash(senha)
            user.token_version = (user.token_version or 0) + 1
            print(f"Usuário {email} promovido a superadmin e senha atualizada.")
        else:
            empresa = Empresa(
                razao_social="Administração do Sistema",
                cnpj=f"ADM-{uuid.uuid4().hex[:14]}",
                setup_concluido=True,
            )
            session.add(empresa)
            await session.flush()
            session.add(Usuario(
                empresa_id=empresa.id,
                nome=nome,
                email=email,
                senha_hash=get_password_hash(senha),
                role=UserRole.ADMIN,
                cargo="Super Administrador",
                is_superuser=True,
            ))
            await seed_modelos_padrao(session, empresa.id, commit=False)
            print(f"Superadmin {email} criado.")

        await session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--email", required=True)
    parser.add_argument("--nome", default="Super Admin")
    args = parser.parse_args()
    asyncio.run(main(args.email.strip().lower(), args.nome))
