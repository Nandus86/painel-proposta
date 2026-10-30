"""seed modelos padrao de proposta (servico, produto, comercial)

Revision ID: a4b5c6d7e8f9
Revises: 9e5f6a7b8c9d
Create Date: 2026-10-30 14:30:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

from app.services.modelos_padrao import MODELOS_PADRAO


revision: str = 'a4b5c6d7e8f9'
down_revision: Union[str, None] = '9e5f6a7b8c9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    empresas = conn.execute(sa.text(
        "SELECT e.id FROM empresas e "
        "LEFT JOIN modelos_proposta m ON m.empresa_id = e.id "
        "GROUP BY e.id "
        "HAVING COUNT(m.id) = 0"
    )).fetchall()

    if not empresas:
        return

    insert_stmt = sa.text(
        "INSERT INTO modelos_proposta (id, empresa_id, titulo, conteudo, created_at, updated_at) "
        "VALUES (:id, :empresa_id, :titulo, :conteudo, NOW(), NOW())"
    )

    for row in empresas:
        empresa_id = row[0]
        for item in MODELOS_PADRAO:
            conn.execute(
                insert_stmt,
                {
                    "id": str(uuid.uuid4()),
                    "empresa_id": str(empresa_id),
                    "titulo": item["titulo"],
                    "conteudo": item["conteudo"],
                }
            )


def downgrade() -> None:
    # Como é seed de dados iniciais que o usuário pode ter editado ou mantido,
    # não removemos em downgrade para evitar perda acidental de dados.
    pass

