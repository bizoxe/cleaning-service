"""create cleanings table

Revision ID: cd97709ee1c6
Revises: 
Create Date: 2025-01-03 18:49:27.702452

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cd97709ee1c6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cleanings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "cleaning_type",
            sa.String(length=100),
            server_default="spot clean",
            nullable=False,
        ),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cleanings")),
    )
    op.create_index(op.f("ix_cleanings_name"), "cleanings", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_cleanings_name"), table_name="cleanings")
    op.drop_table("cleanings")
