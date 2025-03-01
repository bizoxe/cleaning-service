import datetime
from uuid import UUID as PY_UUID

from sqlalchemy import (
    UUID,
    Date,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Time,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from core.models import Base


class UserOffer(Base):
    __tablename__ = "user_offers_for_cleanings"

    offerer_id: Mapped[PY_UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cleaning_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cleanings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
        server_default="pending",
    )
    requested_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    requested_time: Mapped[datetime.time] = mapped_column(Time, nullable=True)

    __table_args__ = (PrimaryKeyConstraint("offerer_id", "cleaning_id"),)

    def __repr__(self) -> str:
        return (
            f"UserOffer: (offerer_id={self.offerer_id!r}, cleaning_id={self.cleaning_id!r}, "
            f"status={self.status!r})"
        )
