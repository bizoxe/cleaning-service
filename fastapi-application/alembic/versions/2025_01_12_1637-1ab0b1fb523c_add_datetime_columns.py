"""add datetime columns

Revision ID: 1ab0b1fb523c
Revises: cd97709ee1c6
Create Date: 2025-01-12 16:37:57.977449

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1ab0b1fb523c"
down_revision: Union[str, None] = "cd97709ee1c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cleanings",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "cleanings",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("cleanings", "updated_at")
    op.drop_column("cleanings", "created_at")

