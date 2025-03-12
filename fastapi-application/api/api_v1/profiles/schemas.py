from enum import StrEnum
from re import compile
from typing import Annotated

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    EmailStr,
    HttpUrl,
)
from pydantic.functional_serializers import PlainSerializer

from utils.pydantic_custom_regex_validator import regex_validator

valid_names = regex_validator(
    pattern=compile(r"^[A-Za-z]+(([,.] |[ '-])[A-Za-z]+)*(\.?)( [IVXLCDM]+)?$"),
    error_message="Only letters are allowed. Do not use special characters or numbers",
)
valid_phone_numbers_belarus = regex_validator(
    pattern=compile(r"^\+375\((29|33|44|25)\)[0-9]{3}-[0-9]{2}-[0-9]{2}$"),
    error_message="Allowable format of mobile phone numbers without spaces: +375(xx)xxx-xx-xx",
)


convert_url_to_string = Annotated[HttpUrl, PlainSerializer(lambda v: str(v), return_type=str)]


class MemberType(StrEnum):
    customer = "customer"
    cleaner = "cleaner"


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
    register_as: MemberType


class ProfileUpdate(ProfileBase):
    first_name: Annotated[str, valid_names] | None
    last_name: Annotated[str, valid_names] | None
    phone_number: Annotated[str, valid_phone_numbers_belarus] | None
    avatar: convert_url_to_string | None


class ProfileInDB(ProfileBase):
    model_config = ConfigDict(use_enum_values=True)
    first_name: str
    last_name: str
    phone_number: str
    avatar: convert_url_to_string | None
    user_id: UUID4
    email: EmailStr
    register_as: MemberType


class ProfilePublic(ProfileInDB):
    pass
