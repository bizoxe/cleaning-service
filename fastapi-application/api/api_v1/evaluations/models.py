import uuid

from sqlalchemy import (
    UUID,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from core.models import Base
from core.models.mixins import IntIdPkMixin


class CleanerEvaluation(IntIdPkMixin, Base):
    owner: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    cleaner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    no_show: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="False")
    headline: Mapped[str] = mapped_column(String(150), nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    professionalism: Mapped[int] = mapped_column(Integer, nullable=True)
    completeness: Mapped[int] = mapped_column(Integer, nullable=True)
    efficiency: Mapped[int] = mapped_column(Integer, nullable=True)
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("owner", "cleaner_id"),)

    def __repr__(self) -> str:
        return f"CleanerEvaluations: (owner={self.owner!r}, cleaner_id={self.cleaner_id!r})"
