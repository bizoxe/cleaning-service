from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    UUID4,
)

from api.api_v1.users.schemas import UserPublic


class CleaningType(str, Enum):
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
    name: str
    price: float
    description: str | None = None
    cleaning_type: CleaningType


class CleaningUpdate(CleaningBase):
    cleaning_type: CleaningType


class CleaningPublic(CleaningBase):
    id: int
    owner: UUID4 | UserPublic


class CleaningInDB(CleaningBase):
    name: str
    price: float
    cleaning_type: CleaningType
    owner: UUID4
