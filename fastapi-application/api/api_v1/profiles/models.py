import uuid

from sqlalchemy import (
    UUID,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from core.models import Base
from core.models.mixins import IntIdPkMixin


class Profile(IntIdPkMixin, Base):
    first_name: Mapped[str] = mapped_column(String(200))
    last_name: Mapped[str] = mapped_column(String(200))
    phone_number: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(150))
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    avatar: Mapped[str] = mapped_column(String(250), nullable=True)
    register_as: Mapped[str] = mapped_column(String(50))
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    def __repr__(self) -> str:
        return (
            f"Profile: (first_name={self.first_name!r}, last_name={self.last_name!r}, "
            f"phone_number={self.phone_number!r}, email={self.email!r})"
        )
