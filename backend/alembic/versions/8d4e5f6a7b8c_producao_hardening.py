"""producao: token_version, segredos cifrados e índices por empresa

Revision ID: 8d4e5f6a7b8c
Revises: 7c3d4e5f6a7b
Create Date: 2026-10-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8d4e5f6a7b8c'
down_revision: Union[str, None] = '7c3d4e5f6a7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEXES = [
    ("ix_propostas_empresa_numero", "propostas", "empresa_id, numero"),
    ("ix_propostas_empresa_created", "propostas", "empresa_id, created_at"),
    ("ix_orcamentos_empresa_numero", "orcamentos", "empresa_id, numero"),
    ("ix_orcamentos_empresa_created", "orcamentos", "empresa_id, created_at"),
    ("ix_itens_proposta_proposta", "itens_proposta", "proposta_id"),
    ("ix_itens_orcamento_orcamento", "itens_orcamento", "orcamento_id"),
    ("ix_clientes_empresa", "clientes", "empresa_id"),
    ("ix_servicos_empresa", "servicos", "empresa_id"),
    ("ix_categorias_empresa", "categorias", "empresa_id"),
    ("ix_usuarios_empresa", "usuarios", "empresa_id"),
    ("ix_usuarios_email_lower", "usuarios", "lower(email)"),
]


def upgrade() -> None:
    op.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0")

    op.alter_column("empresas", "stripe_secret_key", type_=sa.Text(), existing_type=sa.String(255), existing_nullable=True)
    op.alter_column("empresas", "smtp_password", type_=sa.Text(), existing_type=sa.String(255), existing_nullable=True)

    # Chaves Stripe antigas eram gravadas em texto puro: cifra as que ainda não estão cifradas (Fernet = "gAAAA...")
    from app.core.security import encrypt_data

    conn = op.get_bind()
    rows = conn.execute(sa.text(
        "SELECT id, stripe_secret_key FROM empresas "
        "WHERE stripe_secret_key IS NOT NULL AND stripe_secret_key <> '' AND stripe_secret_key NOT LIKE 'gAAAA%'"
    )).fetchall()
    for row_id, value in rows:
        cifrado = encrypt_data(value)
        if cifrado:
            conn.execute(
                sa.text("UPDATE empresas SET stripe_secret_key = :v WHERE id = :id"),
                {"v": cifrado, "id": row_id},
            )

    for name, table, cols in INDEXES:
        op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({cols})")


def downgrade() -> None:
    for name, _table, _cols in INDEXES:
        op.execute(f"DROP INDEX IF EXISTS {name}")
    op.drop_column("usuarios", "token_version")
