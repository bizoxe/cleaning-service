"""
This module contains dependencies for user authentication.
"""

from typing import (
    Annotated,
    Any,
)
from uuid import UUID

from fastapi import (
    Depends,
    HTTPException,
    Security,
    status,
)
from fastapi.security import SecurityScopes
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.http_pwd_bearer import (
    access_token_bearer,
    refresh_token_bearer,
)
from auth.schemas import (
    TokenData,
    TokenDataRefresh,
    UserAuthSchema,
)
from core.models import db_helper
from crud.users import users_crud


async def get_user_by_token_sub(
    user_id: UUID,
    session: AsyncSession,
) -> UserAuthSchema:
    """
    Retrieves a user from the database.
    Args:
        user_id: User ID from the sub payload field of the token.
        session: The database session.

    Returns:
        UserAuthSchema (pydantic model object): The user object.
    """
    if user := await users_crud.get_user_by_id(session=session, user_id=user_id):
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalid (user not found)",
    )


async def get_current_auth_user_for_refresh(
    payload: Annotated[dict[str, Any], Depends(refresh_token_bearer)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> UserAuthSchema:
    """
    Is used to authenticate the user to refresh the access token using
    the refresh token.
    Args:
        payload: Payload from Bearer-token.
        session: The database session.

    Returns:
       UserAuthSchema (pydantic model object): The user object.
    """
    try:
        token_data = TokenDataRefresh(**payload)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials for refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_sub = token_data.sub
    user = await get_user_by_token_sub(user_id=user_sub, session=session)

    return user


async def get_current_auth_user(
    security_scopes: SecurityScopes,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    payload: Annotated[dict[str, Any], Depends(access_token_bearer)],
) -> UserAuthSchema:
    """
    Restrict access to resources for unauthorised users and/or
    users without permission rights.
    Args:
        security_scopes:  The list of the scopes required by dependencies.
        session: The database session.
        payload: Payload from Bearer-token.

    Returns:
        UserAuthSchema (pydantic model object): The user object.
    """
    if security_scopes.scopes:
        authenticate_value = f"Bearer scope='{security_scopes.scope_str}'"
    else:
        authenticate_value = "Bearer"
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        token_data = TokenData(**payload)
    except ValidationError:
        raise credentials_exc
    user = await get_user_by_token_sub(user_id=token_data.sub, session=session)
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    user.logged_in_at = token_data.iat

    return user


async def get_current_active_auth_user(
    current_user: Annotated[
        UserAuthSchema,
        Security(get_current_auth_user, scopes=["read"]),
    ],
) -> UserAuthSchema:
    if current_user.is_active:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Inactive user",
    )


class UserProfilePermissionGetter:
    def __init__(self, register_as: str) -> None:
        self._register_as = register_as

    async def __call__(
        self,
        user_auth: Annotated[UserAuthSchema, Depends(get_current_active_auth_user)],
    ) -> UserAuthSchema:
        if not user_auth.profile_exists:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have a registered profile",
            )
        if self._register_as not in user_auth.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access is only allowed to users registered as a {self._register_as!r}",
            )

        return user_auth
