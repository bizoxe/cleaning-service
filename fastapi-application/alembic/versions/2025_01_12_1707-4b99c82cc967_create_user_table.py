"""create user table

Revision ID: 4b99c82cc967
Revises: 1ab0b1fb523c
Create Date: 2025-01-12 17:07:21.477804

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4b99c82cc967"
down_revision: Union[str, None] = "1ab0b1fb523c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("first_name", sa.String(length=200), nullable=False),
        sa.Column("last_name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=200), nullable=False),
        sa.Column(
            "email_verified",
            sa.Boolean(),
            server_default="False",
            nullable=False,
        ),
        sa.Column("password", sa.LargeBinary(length=200), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="True", nullable=False),
        sa.Column(
            "is_superuser",
            sa.Boolean(),
            server_default="False",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
