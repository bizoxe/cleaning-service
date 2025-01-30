"""
Cleaning views.
"""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
    Security,
    Response,
)
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas import UserAuthSchema
from auth.dependencies import get_current_active_auth_user
from api.api_v1.cleanings.schemas import (
    CleaningCreate,
    CleaningInDB,
    CleaningPublic,
    CleaningUpdate,
)
from core.models import db_helper
from crud.cleanings import cleanings_crud
from api.api_v1.users.schemas import UserPublic
from api.api_v1.cleanings.models import Cleaning
from api.api_v1.cleanings.dependencies import get_one_cleaning

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
    user_auth: Annotated[UserAuthSchema, Depends(get_current_active_auth_user)],
    new_cleaning: CleaningCreate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> CleaningPublic:
    cleaning = CleaningInDB(owner=user_auth.id, **new_cleaning.model_dump())
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
    user_auth: Annotated[UserAuthSchema, Depends(get_current_active_auth_user)],
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
)
async def update_cleaning(
    user_auth: Annotated[
        UserAuthSchema, Security(get_current_active_auth_user, scopes=["modify"])
    ],
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
)
async def delete_cleaning(
    user_auth: Annotated[
        UserAuthSchema, Security(get_current_active_auth_user, scopes=["modify"])
    ],
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
    user_auth: Annotated[UserAuthSchema, Depends(get_current_active_auth_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> list[CleaningPublic]:
    all_cleanings = await cleanings_crud.get_all_cleanings(
        session=session, user_id=user_auth.id
    )

    return all_cleanings
