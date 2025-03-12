from enum import StrEnum
from typing import Annotated

from annotated_types import MinLen
from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
)

from api.api_v1.users.schemas import UserPublic


class CleaningType(StrEnum):
    dust_up = "dust up"
    spot_clean = "spot clean"
    full_clean = "full clean"


class CleaningBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    name: str | None
    price: float | None
    description: str | None
    cleaning_type: CleaningType | None = CleaningType.spot_clean


class CleaningCreate(CleaningBase):
    name: Annotated[str, MinLen(3)]
    price: float
    description: str | None = None
    cleaning_type: CleaningType


class CleaningUpdate(CleaningBase):
    name: Annotated[str, MinLen(3)] | None
    cleaning_type: CleaningType


class CleaningPublic(CleaningBase):
    id: int
    owner: UUID4 | UserPublic


class CleaningInDB(CleaningBase):
    name: str
    price: float
    cleaning_type: CleaningType
    owner: UUID4
