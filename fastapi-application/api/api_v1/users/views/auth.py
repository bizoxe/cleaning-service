from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.users.dependencies import validate_user
from api.api_v1.users.jwt_helpers import (
    create_access_token,
    create_refresh_token,
)
from api.api_v1.users.schemas import (
    UserCreate,
    UserPublic,
)
from auth.dependencies import (
    get_current_active_auth_user,
    get_current_auth_user_for_refresh,
)
from auth.schemas import (
    TokenInfo,
    UserAuthInfo,
    UserAuthSchema,
)
from core.models import db_helper
from crud.users import users_crud
from utils.mailing.helpers import decode_url_safe_token
from utils.mailing.messages import send_verify_email

router = APIRouter(
    tags=["Auth"],
)


@router.post(
    "/signup",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    name="auth:register-new-user",
    summary="new user registration, sending a confirmation email to the user's email",
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
    await send_verify_email(created_user.email)

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


@router.get(
    "/me",
    response_model=UserAuthInfo,
    response_model_exclude_none=True,
    name="auth:user-auth-check-self-info",
    summary="getting of user account information by an authorised user",
)
async def user_auth_check_self_info(
    user_in: Annotated[UserAuthSchema, Depends(get_current_active_auth_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> UserAuthInfo:
    """
    Gets user account information by an authorised user.

    If the user has a profile, the profile information is sent as well.
    """
    user_info = UserAuthInfo(profile=None, **user_in.model_dump())
    if user_in.profile_exists:
        profile = await users_crud.get_user_profile(
            session=session,
            user_id=user_in.id,
        )
        user_info.profile = profile
        return user_info

    return user_info


@router.get(
    "/verify-email/{token}",
    response_model=UserPublic,
    name="auth:verify-user-email",
    summary="user email verification",
)
async def verify_user_email(
    token: str,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> UserPublic:
    """
    Verifies the token sent to the user by email.

    If the token is valid, the verify_email field of the user object received
    from the database is set to True, otherwise an exception will be raised.
    """
    if (token_data := decode_url_safe_token(token=token)) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid",
        )

    if not (
        user := await users_crud.get_user_by_email(
            session=session,
            email=token_data.get("email"),
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    updated_user = await users_crud.update_verify_email_field(session=session, user_id=user.id)

    return UserPublic(**updated_user.as_dict())
