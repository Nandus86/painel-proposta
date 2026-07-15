"""create log_admin table

Revision ID: 45788ad08da4
Revises: a3360f7ee00c
Create Date: 2026-07-15 10:11:33.589192

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45788ad08da4'
down_revision: Union[str, None] = 'a3360f7ee00c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy.dialects import postgresql
    op.create_table(
        'log_admin',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('empresa_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('superadmin_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('acao', sa.String(length=100), nullable=False),
        sa.Column('detalhes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['superadmin_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('log_admin')
