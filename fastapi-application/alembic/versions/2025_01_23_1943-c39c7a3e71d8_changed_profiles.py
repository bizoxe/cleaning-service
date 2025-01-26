"""changed profiles

Revision ID: c39c7a3e71d8
Revises: f852d54d6b98
Create Date: 2025-01-23 19:43:27.863670

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c39c7a3e71d8"
down_revision: Union[str, None] = "f852d54d6b98"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("first_name", sa.String(length=200), nullable=False),
    )
    op.add_column(
        "profiles",
        sa.Column("last_name", sa.String(length=200), nullable=False),
    )
    op.alter_column(
        "profiles",
        "phone_number",
        existing_type=sa.VARCHAR(length=50),
        nullable=False,
    )
    op.drop_index("ix_profiles_id", table_name="profiles")
    op.drop_column("profiles", "full_name")


def downgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column(
            "full_name",
            sa.VARCHAR(length=200),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.create_index("ix_profiles_id", "profiles", ["id"], unique=False)
    op.alter_column(
        "profiles",
        "phone_number",
        existing_type=sa.VARCHAR(length=50),
        nullable=True,
    )
    op.drop_column("profiles", "last_name")
    op.drop_column("profiles", "first_name")
