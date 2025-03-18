from typing import Annotated

from fastapi import (
    Depends,
    HTTPException,
    Path,
    Security,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.cleanings.models import Cleaning
from auth.dependencies import UserProfilePermissionGetter
from auth.schemas import UserAuthSchema
from core.models import db_helper
from crud.cleanings import cleanings_crud


async def get_one_cleaning(
    cleaning_id: Annotated[int, Path(ge=1)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Cleaning:
    cleaning = await cleanings_crud.get_one_cleaning_by_id(
        session=session,
        cleaning_id=cleaning_id,
    )
    if cleaning is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No cleaning found with that id",
        )

    return cleaning


async def check_cleaning_job_owner(
    user_auth: Annotated[UserAuthSchema, Security(UserProfilePermissionGetter("cleaner"), scopes=["modify"])],
    cleaning: Annotated[Cleaning, Depends(get_one_cleaning)],
) -> Cleaning:
    if cleaning.owner != user_auth.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this cleaning job",
        )
    return cleaning
