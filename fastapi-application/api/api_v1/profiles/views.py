from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Security,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.profiles.schemas import (
    ProfileCreate,
    ProfileInDB,
    ProfilePublic,
    ProfileUpdate,
)
from auth.dependencies import get_current_active_auth_user
from auth.schemas import UserAuthSchema
from core.models import db_helper
from crud.profiles import profiles_crud

router = APIRouter(
    tags=["Profiles"],
)


@router.post(
    "",
    response_model=ProfilePublic,
    status_code=status.HTTP_201_CREATED,
    name="profiles:create-profile-for-user-auth",
    summary="creating a profile for an authorized user",
)
async def create_profile_for_user_auth(
    user_auth: Annotated[UserAuthSchema, Depends(get_current_active_auth_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    profile: ProfileCreate,
) -> ProfilePublic:
    user_profile = profile.model_dump()
    user_profile.update(user_id=user_auth.id, email=user_auth.email)
    profile_in_db = ProfileInDB(**user_profile)
    if created_profile := await profiles_crud.create_profile(
        session=session,
        profile_schema=profile_in_db,
    ):
        return created_profile

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="You already have a registered profile",
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
    if user_in.profile_exists:
        profile = await profiles_crud.get_profile_by_user_id(
            session=session,
            user_id=user_in.id,
        )

        return ProfilePublic(**profile.as_dict())

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="You have no registered profile",
    )


@router.put(
    "",
    response_model=ProfilePublic,
    response_model_exclude_none=True,
    name="profiles:update-user-auth-self-profile",
    summary="an authorised user updates his/her profile",
)
async def update_user_auth_self_profile(
    user_in: Annotated[UserAuthSchema, Security(get_current_active_auth_user, scopes=["modify"])],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    update_profile: ProfileUpdate,
) -> ProfilePublic:
    if user_in.profile_exists:
        updated_profile = await profiles_crud.update_user_self_profile(
            session=session,
            user_id=user_in.id,
            schema=update_profile,
        )
        return updated_profile

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="You have no registered profile",
    )
