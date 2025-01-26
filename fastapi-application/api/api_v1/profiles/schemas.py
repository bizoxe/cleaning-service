from re import compile
from typing import Annotated

from pydantic import (
    BaseModel,
    HttpUrl,
    UUID4,
)

from utils.pydantic_custom_regex_validator import regex_validator


valid_names = regex_validator(
    pattern=compile(r"^[A-Za-z]+(([,.] |[ '-])[A-Za-z]+)*(\.?)( [IVXLCDM]+)?$"),
    error_message="Only letters are allowed. Do not use special characters or numbers",
)
valid_phone_numbers_belarus = regex_validator(
    pattern=compile(r"^\+375\((29|33|44|25)\)[0-9]{3}-[0-9]{2}-[0-9]{2}$"),
    error_message="Allowable format of mobile phone numbers without spaces: +375(xx)xxx-xx-xx",
)


class ProfileBase(BaseModel):
    first_name: str | None
    last_name: str | None
    phone_number: str | None
    bio: str | None = None
    avatar: HttpUrl | None = None


class ProfileCreate(ProfileBase):
    first_name: Annotated[str, valid_names]
    last_name: Annotated[str, valid_names]
    phone_number: Annotated[str, valid_phone_numbers_belarus]


class ProfileUpdate(ProfileBase):
    first_name: Annotated[str, valid_names] | None
    last_name: Annotated[str, valid_names] | None
    phone_number: Annotated[str, valid_phone_numbers_belarus] | None


class ProfileInDB(ProfileBase):
    first_name: str
    last_name: str
    phone_number: str
    user_id: UUID4


class ProfilePublic(ProfileBase):
    pass
