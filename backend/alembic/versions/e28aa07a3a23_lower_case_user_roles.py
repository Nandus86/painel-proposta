"""lower case user roles

Revision ID: e28aa07a3a23
Revises: 87959e43485d
Create Date: 2026-07-15 09:53:26.646267

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e28aa07a3a23'
down_revision: Union[str, None] = '87959e43485d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole RENAME VALUE 'ADMIN' TO 'admin'")
    op.execute("ALTER TYPE userrole RENAME VALUE 'GERENTE' TO 'gerente'")
    op.execute("ALTER TYPE userrole RENAME VALUE 'VENDEDOR' TO 'vendedor'")


def downgrade() -> None:
    op.execute("ALTER TYPE userrole RENAME VALUE 'admin' TO 'ADMIN'")
    op.execute("ALTER TYPE userrole RENAME VALUE 'gerente' TO 'GERENTE'")
    op.execute("ALTER TYPE userrole RENAME VALUE 'vendedor' TO 'VENDEDOR'")
