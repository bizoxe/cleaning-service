import datetime
from enum import StrEnum

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    EmailStr,
)

from utils.pagination.schemas import (
    ItemQueryParams,
    SortBy,
)


class UserInfo(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str


class CleaningInfo(BaseModel):
    name: str
    price: float
    description: str | None
    cleaning_type: str
    cleaner: UserInfo


class OfferStatus(StrEnum):
    accepted = "accepted"
    rejected = "rejected"
    pending = "pending"
    completed = "completed"


class OfferBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    offerer_id: UUID4 | None
    cleaning_id: int | None
    status: OfferStatus | None = OfferStatus.pending


class OfferCreate(BaseModel):
    requested_date: datetime.date | None
    requested_time: datetime.time | None


class OfferUpdate(BaseModel):
    status: OfferStatus


class OfferInDB(OfferBase, OfferCreate):
    offerer_id: UUID4
    cleaning_id: int
    status: OfferStatus


class OfferPublic(OfferInDB):
    offerer: UserInfo | None = None
    cleaning: CleaningInfo | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class OfferCompleted(BaseModel):
    status: OfferStatus
    cleaner_id: UUID4


class SortByCleaning(SortBy):
    id = "id"
    price = "price"
    created_at = "created_at"
    updated_at = "updated_at"


class ItemParamsCleaning(ItemQueryParams):
    sort_by: SortByCleaning | None = None
