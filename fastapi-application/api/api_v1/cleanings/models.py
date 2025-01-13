"""
Cleaning models.
"""

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from sqlalchemy import (
    String,
    Text,
    Numeric,
)

from core.models.mixins import IntIdPkMixin
from core.models import Base


class Cleaning(IntIdPkMixin, Base):
    name: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    cleaning_type: Mapped[str] = mapped_column(String(100), server_default="spot clean")
    price: Mapped[float] = mapped_column(Numeric(10, 2))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} (name={self.name})"
