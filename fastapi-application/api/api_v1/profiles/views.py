"""
Profile views.
"""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException,
    Security,
)
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas import UserAuthSchema
from auth.dependencies import get_current_active_auth_user
from core.models import db_helper
from api.api_v1.profiles.schemas import (
    ProfileCreate,
    ProfilePublic,
    ProfileInDB,
    ProfileUpdate,
)
from crud.profiles import profiles_crud

router = APIRouter(
    tags=["Profiles"],
)


@router.post(
    "",
    response_model=ProfilePublic,
    status_code=status.HTTP_201_CREATED,
    name="profiles:create-profile-for-user-auth",
    summary="create a profile for an authorised user",
)
async def create_profile_for_user_auth(
    user_auth: Annotated[UserAuthSchema, Depends(get_current_active_auth_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    profile: ProfileCreate,
) -> ProfilePublic:
    """
    Creates a profile for a user.
    """
    user_profile = profile.model_dump()
    user_profile.update(user_id=user_auth.id)
    profile_in_db = ProfileInDB(**user_profile)
    if created_profile := await profiles_crud.create_profile(
        session=session,
        profile_schema=profile_in_db,
    ):
        return created_profile

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="You have already a profile in the system",
    )


@router.get(
    "",
    response_model=ProfilePublic,
    response_model_exclude_none=True,
    name="profiles:get-user-auth-self-profile",
    summary="an authorised user receives information about his or her profile",
)
async def get_user_auth_self_profile(
    user_in: Annotated[UserAuthSchema, Depends(get_current_active_auth_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> ProfilePublic:
    """
    Gets user  profile information.
    """
    if profile := await profiles_crud.get_profile_by_user_id(
        session=session, user_id=user_in.id
    ):

        return ProfilePublic(**profile.as_dict())

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="The user profile is not in the system. Create a profile",
    )


@router.put(
    "",
    response_model=ProfilePublic,
    response_model_exclude_none=True,
    name="profiles:update-user-auth-self-profile",
    summary="an authorised user updates his/her profile",
)
async def update_user_auth_self_profile(
    user_in: Annotated[
        UserAuthSchema, Security(get_current_active_auth_user, scopes=["modify"])
    ],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    update_profile: ProfileUpdate,
) -> ProfilePublic:
    """
    Updates the user's profile.
    """
    if updated_profile := await profiles_crud.update_user_self_profile(
        session=session,
        user_id=user_in.id,
        schema=update_profile,
    ):
        return updated_profile

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="The user profile is not in the system. Create a profile",
    )
