from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Security,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.users.schemas import (
    UserPublic,
    UserUpdate,
    UserUpdatePassword,
)
from auth.dependencies import get_current_active_auth_user
from auth.schemas import UserAuthSchema
from auth.utils.auth_utils import hash_password
from core.models import db_helper
from crud.users import users_crud

router = APIRouter(
    tags=["Users"],
)


@router.patch(
    "/reset-password",
    response_model=UserPublic,
    name="users:reset-user-password",
    summary="password update for an authorised user",
)
async def reset_user_password(
    user_auth: Annotated[UserAuthSchema, Security(get_current_active_auth_user, scopes=["modify"])],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    update_pwd: UserUpdatePassword,
) -> UserPublic:
    str_pwd_to_bytes: bytes = hash_password(
        plaintext_password=update_pwd.password,
    )
    user = await users_crud.reset_password(
        user_id=user_auth.id,
        new_pwd=str_pwd_to_bytes,
        session=session,
    )

    return UserPublic(**user.as_dict())


@router.patch(
    "/update-email",
    response_model=UserPublic,
    name="users:update-self-email",
    summary="email update for an authorised user",
)
async def update_self_email(
    user_auth: Annotated[UserAuthSchema, Security(get_current_active_auth_user, scopes=["modify"])],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    new_email: UserUpdate,
) -> UserPublic:
    if to_update := await users_crud.update_email(
        user_in=user_auth,
        new_email=new_email.email,
        session=session,
    ):
        return UserPublic(**to_update.as_dict())

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Email already registered",
    )
