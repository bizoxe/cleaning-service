"""
User auth views.
"""

from typing import Annotated

from fastapi import (
    APIRouter,
    status,
    Depends,
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.users.schemas import (
    UserPublic,
    UserCreate,
)
from core.models import db_helper
from crud.users import users_crud
from auth.schemas import (
    UserAuthSchema,
    TokenInfo,
)
from api.api_v1.users.dependencies import validate_user
from api.api_v1.users.jwt_helpers import (
    create_access_token,
    create_refresh_token,
)
from auth.dependencies import (
    get_current_auth_user_for_refresh,
)


router = APIRouter(
    tags=["Auth"],
)


@router.post(
    "/signup",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    name="auth:register-new-user",
    summary="new user registration",
)
async def register_user_account(
    new_user: UserCreate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> UserPublic:
    created_user = await users_crud.create_user(session=session, user_schema=new_user)
    if created_user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return created_user


@router.post(
    "/signin",
    response_model=TokenInfo,
    name="auth:auth-user-issue-jwt",
    summary="user login, issue access and refresh tokens",
)
async def auth_user_issue_jwt(
    user_in: Annotated[UserAuthSchema, Depends(validate_user)],
) -> TokenInfo:
    access_token = create_access_token(user=user_in)
    refresh_token = create_refresh_token(user=user_in)

    return TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh-jwt",
    response_model=TokenInfo,
    response_model_exclude_none=True,
    name="auth:auth-user-refresh-jwt",
    summary="refresh access token using refresh token",
)
async def auth_user_refresh_jwt(
    user_in: Annotated[UserAuthSchema, Depends(get_current_auth_user_for_refresh)],
) -> TokenInfo:
    access_token = create_access_token(user=user_in)

    return TokenInfo(
        access_token=access_token,
    )
