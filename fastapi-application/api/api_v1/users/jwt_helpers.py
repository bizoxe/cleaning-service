"""
This module contains helper functions for issuing
access and refresh tokens.
"""

from datetime import timedelta
from typing import Any

from auth.schemas import UserAuthSchema
from auth.utils.auth_utils import encode_jwt
from core.config import settings

TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def create_jwt(
    token_type: str,
    token_data: dict[str, Any],
    expire_minutes: int = settings.auth_jwt.access_token_expire_minutes,
    expire_timedelta: timedelta | None = None,
) -> str:
    jwt_payload = {TOKEN_TYPE_FIELD: token_type}
    jwt_payload.update(token_data)

    return encode_jwt(
        payload=jwt_payload,
        expire_minutes=expire_minutes,
        expire_timedelta=expire_timedelta,
    )


def create_access_token(
    user: UserAuthSchema,
    extra: dict[str, Any] | None = None,
) -> str:
    jwt_payload = {
        "sub": str(user.id),
        "email": user.email,
        "scopes": user.permissions,
    }
    if extra is not None:
        jwt_payload.update(**extra)

    return create_jwt(
        token_type=ACCESS_TOKEN_TYPE,
        token_data=jwt_payload,
        expire_minutes=settings.auth_jwt.access_token_expire_minutes,
    )


def create_refresh_token(user: UserAuthSchema) -> str:
    jwt_payload = {"sub": str(user.id)}

    return create_jwt(
        token_type=REFRESH_TOKEN_TYPE,
        token_data=jwt_payload,
        expire_timedelta=timedelta(
            days=settings.auth_jwt.refresh_token_expire_days,
        ),
    )
