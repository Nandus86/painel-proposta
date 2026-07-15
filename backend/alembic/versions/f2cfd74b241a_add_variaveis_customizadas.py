"""add_variaveis_customizadas

Revision ID: f2cfd74b241a
Revises: 45788ad08da4
Create Date: 2026-07-15 11:43:15.483432

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2cfd74b241a'
down_revision: Union[str, None] = '45788ad08da4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('variaveis_customizadas',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('empresa_id', sa.UUID(), nullable=False),
    sa.Column('tag', sa.String(length=100), nullable=False),
    sa.Column('nome', sa.String(length=255), nullable=False),
    sa.Column('valor_padrao', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('variaveis_customizadas')
