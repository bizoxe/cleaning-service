from datetime import datetime

from pydantic import (
    BaseModel,
    UUID4,
    EmailStr,
    ConfigDict,
)


class UserAuthSchema(BaseModel):
    model_config = ConfigDict(strict=True)
    id: UUID4
    email: EmailStr
    email_verified: bool
    is_active: bool
    permissions: list[str]
    logged_in_at: datetime | None = None


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
