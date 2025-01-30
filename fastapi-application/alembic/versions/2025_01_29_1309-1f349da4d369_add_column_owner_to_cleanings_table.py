"""add column owner to cleanings table

Revision ID: 1f349da4d369
Revises: 36aff9fc6551
Create Date: 2025-01-29 13:09:29.990210

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1f349da4d369"
down_revision: Union[str, None] = "36aff9fc6551"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cleanings", sa.Column("owner", sa.UUID(), nullable=False))
    op.create_foreign_key(
        op.f("fk_cleanings_owner_users"),
        "cleanings",
        "users",
        ["owner"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_cleanings_owner_users"), "cleanings", type_="foreignkey"
    )
    op.drop_column("cleanings", "owner")
