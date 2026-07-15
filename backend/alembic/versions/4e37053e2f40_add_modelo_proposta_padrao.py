"""add modelo_proposta_padrao

Revision ID: 4e37053e2f40
Revises: c392a230099f
Create Date: 2026-06-16 08:29:11.416398

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e37053e2f40'
down_revision: Union[str, None] = 'c392a230099f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('empresas', sa.Column('modelo_proposta_padrao', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('empresas', 'modelo_proposta_padrao')
