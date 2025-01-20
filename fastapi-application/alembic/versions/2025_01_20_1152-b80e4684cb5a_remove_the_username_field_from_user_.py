"""remove the username field from user model

Revision ID: b80e4684cb5a
Revises: 16d311823a38
Create Date: 2025-01-20 11:52:51.611841

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b80e4684cb5a"
down_revision: Union[str, None] = "16d311823a38"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "username")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "username",
            sa.VARCHAR(length=200),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
