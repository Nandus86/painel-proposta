"""lower case remaining enums

Revision ID: a3360f7ee00c
Revises: e28aa07a3a23
Create Date: 2026-07-15 10:04:16.975042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3360f7ee00c'
down_revision: Union[str, None] = 'e28aa07a3a23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # statusproposta
    op.execute("ALTER TYPE statusproposta RENAME VALUE 'RASCUNHO' TO 'rascunho'")
    op.execute("ALTER TYPE statusproposta RENAME VALUE 'ENVIADA' TO 'enviada'")
    op.execute("ALTER TYPE statusproposta RENAME VALUE 'ACEITA' TO 'aceita'")
    op.execute("ALTER TYPE statusproposta RENAME VALUE 'RECUSADA' TO 'recusada'")
    op.execute("ALTER TYPE statusproposta RENAME VALUE 'EXPIRADA' TO 'expirada'")
    
    # statusorcamento
    op.execute("ALTER TYPE statusorcamento RENAME VALUE 'RASCUNHO' TO 'rascunho'")
    op.execute("ALTER TYPE statusorcamento RENAME VALUE 'ENVIADO' TO 'enviado'")
    op.execute("ALTER TYPE statusorcamento RENAME VALUE 'APROVADO' TO 'aprovado'")
    op.execute("ALTER TYPE statusorcamento RENAME VALUE 'REJEITADO' TO 'rejeitado'")
    op.execute("ALTER TYPE statusorcamento RENAME VALUE 'VENCIDO' TO 'vencido'")
    
    # tiposervico
    op.execute("ALTER TYPE tiposervico RENAME VALUE 'PRODUTO' TO 'produto'")
    op.execute("ALTER TYPE tiposervico RENAME VALUE 'SERVICO' TO 'servico'")
    op.execute("ALTER TYPE tiposervico RENAME VALUE 'RECORRENTE' TO 'recorrente'")


def downgrade() -> None:
    # statusproposta
    op.execute("ALTER TYPE statusproposta RENAME VALUE 'rascunho' TO 'RASCUNHO'")
    op.execute("ALTER TYPE statusproposta RENAME VALUE 'enviada' TO 'ENVIADA'")
    op.execute("ALTER TYPE statusproposta RENAME VALUE 'aceita' TO 'ACEITA'")
    op.execute("ALTER TYPE statusproposta RENAME VALUE 'recusada' TO 'RECUSADA'")
    op.execute("ALTER TYPE statusproposta RENAME VALUE 'expirada' TO 'EXPIRADA'")
    
    # statusorcamento
    op.execute("ALTER TYPE statusorcamento RENAME VALUE 'rascunho' TO 'RASCUNHO'")
    op.execute("ALTER TYPE statusorcamento RENAME VALUE 'enviado' TO 'ENVIADO'")
    op.execute("ALTER TYPE statusorcamento RENAME VALUE 'aprovado' TO 'APROVADO'")
    op.execute("ALTER TYPE statusorcamento RENAME VALUE 'rejeitado' TO 'REJEITADO'")
    op.execute("ALTER TYPE statusorcamento RENAME VALUE 'vencido' TO 'VENCIDO'")
    
    # tiposervico
    op.execute("ALTER TYPE tiposervico RENAME VALUE 'produto' TO 'PRODUTO'")
    op.execute("ALTER TYPE tiposervico RENAME VALUE 'servico' TO 'SERVICO'")
    op.execute("ALTER TYPE tiposervico RENAME VALUE 'recorrente' TO 'RECORRENTE'")
