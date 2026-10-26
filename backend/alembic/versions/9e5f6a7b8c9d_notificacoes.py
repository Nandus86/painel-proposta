"""notificacoes

Revision ID: 9e5f6a7b8c9d
Revises: 8d4e5f6a7b8c
Create Date: 2026-10-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '9e5f6a7b8c9d'
down_revision: Union[str, None] = '8d4e5f6a7b8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notificacoes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('empresa_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('empresas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tipo', sa.String(30), nullable=False),
        sa.Column('titulo', sa.String(255), nullable=False),
        sa.Column('mensagem', sa.Text(), nullable=True),
        sa.Column('link', sa.String(500), nullable=True),
        sa.Column('referencia_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('lida', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_notificacoes_usuario_lida', 'notificacoes', ['usuario_id', 'lida', 'created_at'])
    op.create_index('ix_notificacoes_referencia', 'notificacoes', ['referencia_id', 'tipo'])


def downgrade() -> None:
    op.drop_index('ix_notificacoes_referencia', table_name='notificacoes')
    op.drop_index('ix_notificacoes_usuario_lida', table_name='notificacoes')
    op.drop_table('notificacoes')
