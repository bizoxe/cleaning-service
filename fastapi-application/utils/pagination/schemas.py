from typing import (
    TypeVar,
    Generic,
)
from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    AnyHttpUrl,
)

M = TypeVar("M")


class PaginatedResponse(BaseModel, Generic[M]):
    count: int = Field(description="Number of items returned in response")
    next_cursor: str | None = Field(
        None, description="Token to get items after the current page if any"
    )
    next_page: AnyHttpUrl | None = Field(
        None, description="Url of the next page if it exists"
    )
    previous_cursor: str | None = Field(
        None, description="Token to get items before the current page if any"
    )
    previous_page: AnyHttpUrl | None = Field(
        None, description="Url of the previous page if it exists"
    )
    items: list[M] = Field(
        description="List of items returned in the response based on specified criteria"
    )


class SortBy(str, Enum):
    pass


class ItemQueryParams(BaseModel):
    sort_by: SortBy | None
    descending: bool = False
