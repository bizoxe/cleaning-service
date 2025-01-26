"""reset the database because of conflicts

Revision ID: 7ae3d425a9f9
Revises: 9a2404c97e70, c39c7a3e71d8
Create Date: 2025-01-26 12:18:33.451954

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7ae3d425a9f9"
down_revision: Union[str, None] = ("9a2404c97e70", "c39c7a3e71d8")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
