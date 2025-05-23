from re import compile
from typing import Annotated

from pydantic import (
    UUID4,
    BaseModel,
    EmailStr,
    model_validator,
)
from typing_extensions import Self

from utils.pydantic_custom_regex_validator import regex_validator

valid_pwd = regex_validator(
    pattern=compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"),
    error_message="The password must contain a minimum of eight characters, at least one uppercase letter, one "
    "lowercase letter, one number and one special character",
)


class UserBase(BaseModel):
    email: EmailStr | None
    email_verified: bool = False
    is_active: bool = True


class UserCreate(BaseModel):
    email: EmailStr
    password: Annotated[str, valid_pwd]
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords don't match")

        return self


class UserUpdate(BaseModel):
    email: EmailStr


class UserUpdatePassword(BaseModel):
    password: Annotated[str, valid_pwd]
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords don't match")

        return self


class UserInDB(UserBase):
    email: EmailStr
    password: bytes
    role_id: int = 1


class UserPublic(UserBase):
    id: UUID4
