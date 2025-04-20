"""recreate all tables

Revision ID: 84d9b87f477a
Revises: 6a77f719ea82
Create Date: 2025-04-10 15:27:47.970504

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "84d9b87f477a"
down_revision: Union[str, None] = "6a77f719ea82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permissions")),
    )
    op.create_index(op.f("ix_permissions_id"), "permissions", ["id"], unique=False)
    op.create_index(op.f("ix_permissions_name"), "permissions", ["name"], unique=True)
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)
    op.create_table(
        "role_permission",
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("permission_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name=op.f("fk_role_permission_permission_id_permissions"),
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name=op.f("fk_role_permission_role_id_roles"),
        ),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
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
            "profile_exists",
            sa.Boolean(),
            server_default="False",
            nullable=False,
        ),
        sa.Column(
            "role_id",
            sa.Integer(),
            server_default=sa.text("1"),
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
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name=op.f("fk_users_role_id_roles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_table(
        "cleaner_evaluations",
        sa.Column("owner", sa.UUID(), nullable=False),
        sa.Column("cleaner_id", sa.UUID(), nullable=False),
        sa.Column("no_show", sa.Boolean(), server_default="False", nullable=False),
        sa.Column("headline", sa.String(length=150), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("professionalism", sa.Integer(), nullable=True),
        sa.Column("completeness", sa.Integer(), nullable=True),
        sa.Column("efficiency", sa.Integer(), nullable=True),
        sa.Column("overall_rating", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["cleaner_id"],
            ["users.id"],
            name=op.f("fk_cleaner_evaluations_cleaner_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cleaner_evaluations")),
        sa.UniqueConstraint(
            "owner",
            "cleaner_id",
            name=op.f("uq_cleaner_evaluations_owner_cleaner_id"),
        ),
    )
    op.create_index(
        op.f("ix_cleaner_evaluations_cleaner_id"),
        "cleaner_evaluations",
        ["cleaner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cleaner_evaluations_owner"),
        "cleaner_evaluations",
        ["owner"],
        unique=False,
    )
    op.create_table(
        "cleanings",
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "cleaning_type",
            sa.String(length=100),
            server_default="spot clean",
            nullable=False,
        ),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("owner", sa.UUID(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["owner"],
            ["users.id"],
            name=op.f("fk_cleanings_owner_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cleanings")),
    )
    op.create_index(op.f("ix_cleanings_name"), "cleanings", ["name"], unique=False)
    op.create_table(
        "profiles",
        sa.Column("first_name", sa.String(length=200), nullable=False),
        sa.Column("last_name", sa.String(length=200), nullable=False),
        sa.Column("phone_number", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar", sa.String(length=250), nullable=True),
        sa.Column("register_as", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_profiles")),
    )
    op.create_table(
        "user_offers_for_cleanings",
        sa.Column("offerer_id", sa.UUID(), nullable=False),
        sa.Column("cleaning_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=120),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("requested_date", sa.Date(), nullable=True),
        sa.Column("requested_time", sa.Time(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["cleaning_id"],
            ["cleanings.id"],
            name=op.f("fk_user_offers_for_cleanings_cleaning_id_cleanings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["offerer_id"],
            ["users.id"],
            name=op.f("fk_user_offers_for_cleanings_offerer_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "offerer_id",
            "cleaning_id",
            name=op.f("pk_user_offers_for_cleanings"),
        ),
    )
    op.create_index(
        op.f("ix_user_offers_for_cleanings_cleaning_id"),
        "user_offers_for_cleanings",
        ["cleaning_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_offers_for_cleanings_offerer_id"),
        "user_offers_for_cleanings",
        ["offerer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_offers_for_cleanings_status"),
        "user_offers_for_cleanings",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_user_offers_for_cleanings_status"),
        table_name="user_offers_for_cleanings",
    )
    op.drop_index(
        op.f("ix_user_offers_for_cleanings_offerer_id"),
        table_name="user_offers_for_cleanings",
    )
    op.drop_index(
        op.f("ix_user_offers_for_cleanings_cleaning_id"),
        table_name="user_offers_for_cleanings",
    )
    op.drop_table("user_offers_for_cleanings")
    op.drop_table("profiles")
    op.drop_index(op.f("ix_cleanings_name"), table_name="cleanings")
    op.drop_table("cleanings")
    op.drop_index(op.f("ix_cleaner_evaluations_owner"), table_name="cleaner_evaluations")
    op.drop_index(
        op.f("ix_cleaner_evaluations_cleaner_id"),
        table_name="cleaner_evaluations",
    )
    op.drop_table("cleaner_evaluations")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_table("role_permission")
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_index(op.f("ix_roles_id"), table_name="roles")
    op.drop_table("roles")
    op.drop_index(op.f("ix_permissions_name"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_id"), table_name="permissions")
    op.drop_table("permissions")
