"""add_uazapi_fields

Revision ID: 7c3d4e5f6a7b
Revises: 6b2c3d4e5f6a
Create Date: 2026-08-01 11:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '7c3d4e5f6a7b'
down_revision: Union[str, None] = '6b2c3d4e5f6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sistema_config', sa.Column('uazapi_base_url', sa.String(255), nullable=True))
    op.add_column('sistema_config', sa.Column('uazapi_admin_token', sa.Text(), nullable=True))

    op.add_column('empresas', sa.Column('uazapi_instance_id', sa.String(100), nullable=True))
    op.add_column('empresas', sa.Column('uazapi_instance_token', sa.Text(), nullable=True))
    op.add_column('empresas', sa.Column('whatsapp_numero', sa.String(20), nullable=True))
    op.add_column('empresas', sa.Column('whatsapp_status', sa.String(20), nullable=True))
    op.add_column('empresas', sa.Column('whatsapp_mensagem_padrao', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('empresas', 'whatsapp_mensagem_padrao')
    op.drop_column('empresas', 'whatsapp_status')
    op.drop_column('empresas', 'whatsapp_numero')
    op.drop_column('empresas', 'uazapi_instance_token')
    op.drop_column('empresas', 'uazapi_instance_id')
    op.drop_column('sistema_config', 'uazapi_admin_token')
    op.drop_column('sistema_config', 'uazapi_base_url')
