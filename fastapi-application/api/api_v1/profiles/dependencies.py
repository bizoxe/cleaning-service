from typing import Annotated

from fastapi import (
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_active_auth_user
from auth.schemas import UserAuthProfile, UserAuthSchema
from core.models import db_helper
from crud.profiles import profiles_crud


async def get_user_profile_or_http_exception(
    user_auth: Annotated[UserAuthSchema, Depends(get_current_active_auth_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> UserAuthProfile:
    """
    Gets the user profile.

    If the profile does not exist, redirects to the profile creation url.
    """
    if user_auth.profile_exists:
        profile = await profiles_crud.get_profile_by_user_id(
            session=session,
            user_id=user_auth.id,
        )
        return UserAuthProfile(**profile.as_dict())

    raise HTTPException(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        detail="You do not have a registered profile",
        headers={"Location": "/api/v1/profiles"},
    )
