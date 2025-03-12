from datetime import datetime

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    EmailStr,
    HttpUrl,
)


class UserAuthSchema(BaseModel):
    model_config = ConfigDict(strict=True)
    id: UUID4
    email: EmailStr
    email_verified: bool
    is_active: bool
    profile_exists: bool
    permissions: list[str]
    logged_in_at: datetime | None = None


class UserAuthProfile(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    email: EmailStr
    bio: str | None
    avatar: HttpUrl | None
    register_as: str
    user_id: UUID4


class UserAuthInfo(BaseModel):
    email: EmailStr
    email_verified: bool
    logged_in_at: datetime
    profile: UserAuthProfile | None


class TokenMeta(BaseModel):
    type: str
    sub: UUID4
    jti: str
    iat: datetime
    exp: datetime


class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"


class TokenData(TokenMeta):
    email: EmailStr
    scopes: list[str] = []


class TokenDataRefresh(TokenMeta):
    pass
