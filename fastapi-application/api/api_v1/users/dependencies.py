from typing import Annotated

from fastapi import (
    Depends,
    Form,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas import UserAuthSchema
from auth.utils.auth_utils import verify_password
from core.models import db_helper
from crud.users import users_crud


async def validate_user(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> UserAuthSchema:
    """
    User validation at login.
    Args:
        username: Mail is used instead of username.
        password: User password.
        session: The database session.

    Returns:
        UserAuthSchema (pydantic model object): The user object.
    """
    unauthorized_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )

    if not (
        user := await users_crud.get_user_by_email(
            session=session,
            email=username,
        )
    ):
        raise unauthorized_exc

    if not verify_password(
        plaintext_password=password,
        hashed_password=user.password,
    ):
        raise unauthorized_exc

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User inactive",
        )

    return UserAuthSchema(
        id=user.id,
        email=user.email,
        email_verified=user.email_verified,
        is_active=user.is_active,
        profile_exists=user.profile_exists,
        permissions=[perm.name for perm in user.role.permissions],
    )
