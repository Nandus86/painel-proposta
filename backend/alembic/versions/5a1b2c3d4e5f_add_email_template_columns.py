"""add_email_template_columns

Revision ID: 5a1b2c3d4e5f
Revises: f2cfd74b241a
Create Date: 2026-08-01 11:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '5a1b2c3d4e5f'
down_revision: Union[str, None] = 'f2cfd74b241a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('empresas', sa.Column('email_assunto_padrao', sa.String(length=255), nullable=True))
    op.add_column('empresas', sa.Column('email_corpo_padrao', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('empresas', 'email_corpo_padrao')
    op.drop_column('empresas', 'email_assunto_padrao')
