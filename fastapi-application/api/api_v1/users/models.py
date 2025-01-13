"""
User models.
"""

import uuid

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from sqlalchemy import (
    UUID,
    String,
    Boolean,
    LargeBinary,
)

from core.models import Base


class User(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(200))
    last_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, server_default="False")
    password: Mapped[bytes] = mapped_column(LargeBinary(200))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="True")
    is_superuser: Mapped[bool] = mapped_column(Boolean, server_default="False")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} (id={self.id})"
