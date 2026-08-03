"""add_planos_table_and_empresa_config

Revision ID: 6b2c3d4e5f6a
Revises: 5a1b2c3d4e5f
Create Date: 2026-08-01 11:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '6b2c3d4e5f6a'
down_revision: Union[str, None] = '5a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'planos',
        sa.Column('slug', sa.String(50), nullable=False),
        sa.Column('nome', sa.String(100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('preco_mensal', sa.Numeric(10, 2), nullable=True),
        sa.Column('preco_anual', sa.Numeric(10, 2), nullable=True),
        sa.Column('moeda', sa.String(3), server_default='BRL', nullable=False),
        sa.Column('max_usuarios', sa.Integer(), nullable=True),
        sa.Column('max_propostas_mes', sa.Integer(), nullable=True),
        sa.Column('ai_credits_limit', sa.Integer(), server_default='20', nullable=False),
        sa.Column('permite_dominio_proprio', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('ordem', sa.Integer(), server_default='0', nullable=False),
        sa.Column('ativo', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('destaque', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('slug')
    )

    op.add_column('empresas', sa.Column('plano_solicitado', sa.String(50), nullable=True))
    op.add_column('empresas', sa.Column('setup_concluido', sa.Boolean(), server_default='false', nullable=False))

    default_planos = [
        ('gratuito', 'Gratuito', 'Ideal para começar', None, None, 1, 3, 20, False, 0, True, True),
        ('inicial', 'Inicial', 'Para pequenas empresas', 39.00, 429.00, 2, 20, 50, False, 1, True, False),
        ('pro', 'Pro', 'Para empresas em crescimento', 69.00, 759.00, 5, 50, 100, True, 2, True, True),
        ('empresarial', 'Empresarial', 'Para grandes operações', 129.00, 1419.00, None, None, 200, True, 3, True, False),
    ]
    for slug, nome, desc, mensal, anual, max_usr, max_prop, ai, dominio, ordem, ativo, destaque in default_planos:
        m_str = "NULL" if mensal is None else str(mensal)
        a_str = "NULL" if anual is None else str(anual)
        usr_str = "NULL" if max_usr is None else str(max_usr)
        prop_str = "NULL" if max_prop is None else str(max_prop)
        dom_str = "true" if dominio else "false"
        atv_str = "true" if ativo else "false"
        des_str = "true" if destaque else "false"
        op.execute(
            f"INSERT INTO planos (slug, nome, descricao, preco_mensal, preco_anual, moeda, "
            f"max_usuarios, max_propostas_mes, ai_credits_limit, permite_dominio_proprio, "
            f"ordem, ativo, destaque) VALUES "
            f"('{slug}', '{nome}', '{desc}', {m_str}, {a_str}, 'BRL', {usr_str}, {prop_str}, {ai}, {dom_str}, {ordem}, {atv_str}, {des_str})"
        )


def downgrade() -> None:
    op.drop_column('empresas', 'setup_concluido')
    op.drop_column('empresas', 'plano_solicitado')
    op.drop_table('planos')
