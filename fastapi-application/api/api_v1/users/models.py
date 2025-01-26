"""
User models.
"""

import uuid

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy import (
    Table,
    Column,
    Integer,
    ForeignKey,
    UUID,
    String,
    Boolean,
    LargeBinary,
    text,
)

from core.models import Base


role_permission = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id")),
    Column("permission_id", Integer, ForeignKey("permissions.id")),
)


class User(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, server_default="False")
    password: Mapped[bytes] = mapped_column(LargeBinary(200))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="True")
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.id"),
        server_default=text("1"),
    )
    role = relationship("Role", back_populates="users", lazy="selectin")
    profile = relationship("Profile", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"User: (id={self.id!r}, email={self.email!r},"
            f" is_active={self.is_active!r}, role_permissions={[perm.name for perm in self.role.permissions]!r})"
        )


class Role(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    permissions = relationship(
        "Permission",
        secondary=role_permission,
        back_populates="roles",
        lazy="selectin",
    )
    users = relationship("User", back_populates="role")


class Permission(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    roles = relationship(
        "Role", secondary=role_permission, back_populates="permissions"
    )
