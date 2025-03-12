from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    Security,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.cleanings.dependencies import get_one_cleaning
from api.api_v1.cleanings.models import Cleaning
from api.api_v1.cleanings.schemas import (
    CleaningCreate,
    CleaningInDB,
    CleaningPublic,
    CleaningUpdate,
)
from api.api_v1.profiles.dependencies import (
    get_user_profile_or_http_exception,
)
from api.api_v1.users.schemas import UserPublic
from auth.dependencies import UserProfilePermissionGetter
from auth.schemas import UserAuthProfile, UserAuthSchema
from core.models import db_helper
from crud.cleanings import cleanings_crud

router = APIRouter(
    tags=["Cleanings"],
)


@router.post(
    "",
    response_model=CleaningPublic,
    status_code=status.HTTP_201_CREATED,
    name="cleanings:create-cleaning",
    summary="creating a new cleaning for the user",
)
async def create_new_cleaning(
    profile: Annotated[UserAuthProfile, Depends(get_user_profile_or_http_exception)],
    new_cleaning: CleaningCreate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> CleaningPublic:
    """
    Creates cleaning.

    If the user does not have a profile, the user is redirected to create a profile.
    """
    if profile.register_as != "cleaner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users registered as a cleaner can create cleanings",
        )
    cleaning = CleaningInDB(owner=profile.user_id, **new_cleaning.model_dump())
    created_cleaning = await cleanings_crud.create_cleaning(
        session=session,
        cleaning=cleaning,
    )

    return created_cleaning


@router.get(
    "/{cleaning_id}",
    response_model=CleaningPublic,
    name="cleanings:get-cleaning-by-id",
    summary="getting one cleaning by its identifier",
)
async def get_cleaning_by_id(
    user_auth: Annotated[UserAuthSchema, Depends(UserProfilePermissionGetter("cleaner"))],
    cleaning: Annotated[Cleaning, Depends(get_one_cleaning)],
) -> CleaningPublic:
    cleaning_by_id = cleaning.as_dict()
    cleaning_by_id.update(owner=UserPublic(**user_auth.model_dump()))

    return CleaningPublic(**cleaning_by_id)


@router.put(
    "/{cleaning_id}",
    response_model=CleaningPublic,
    name="cleanings:update-cleaning",
    summary="updating the cleaning by its identifier",
    dependencies=[Security(UserProfilePermissionGetter("cleaner"), scopes=["modify"])],
)
async def update_cleaning(
    cleaning: Annotated[Cleaning, Depends(get_one_cleaning)],
    cleaning_update: CleaningUpdate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> CleaningPublic:
    updated_cleaning = await cleanings_crud.update_cleaning(
        session=session,
        db_obj=cleaning,
        to_update=cleaning_update,
    )

    return updated_cleaning


@router.delete(
    "/{cleaning_id}",
    name="cleanings:delete-cleaning",
    summary="deleting the cleaning by its identifier",
    dependencies=[Security(UserProfilePermissionGetter("cleaner"), scopes=["modify"])],
)
async def delete_cleaning(
    cleaning: Annotated[Cleaning, Depends(get_one_cleaning)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Response:
    await cleanings_crud.delete_cleaning(session=session, db_obj=cleaning)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "",
    response_model=list[CleaningPublic],
    name="cleanings:get-all-cleanings",
    summary="getting user all self cleanings",
)
async def get_user_all_cleanings(
    user_auth: Annotated[UserAuthSchema, Depends(UserProfilePermissionGetter("cleaner"))],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> list[CleaningPublic]:
    all_cleanings = await cleanings_crud.get_all_cleanings(
        session=session,
        user_id=user_auth.id,
    )

    return [CleaningPublic(**cl.as_dict()) for cl in all_cleanings]
