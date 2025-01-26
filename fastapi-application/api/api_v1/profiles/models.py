"""
Profile models.
"""

import uuid

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from sqlalchemy import (
    String,
    Text,
    UUID,
    ForeignKey,
)

from core.models.mixins import IntIdPkMixin
from core.models import Base


class Profile(IntIdPkMixin, Base):
    first_name: Mapped[str] = mapped_column(String(200))
    last_name: Mapped[str] = mapped_column(String(200))
    phone_number: Mapped[str] = mapped_column(String(50))
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    avatar: Mapped[str] = mapped_column(String(250), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        default=uuid.uuid4,
    )

    def __repr__(self) -> str:
        return (f"Profile: (first_name={self.first_name!r}, last_name={self.last_name!r}, "
                f"phone_number={self.phone_number!r})")
