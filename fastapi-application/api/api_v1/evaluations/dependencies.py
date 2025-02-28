from typing import Annotated
from uuid import UUID

from fastapi import (
    Depends,
    HTTPException,
    Path,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.cleanings.schemas import CleaningPublic
from api.api_v1.evaluations.schemas import CleanerInfo
from core.models import db_helper
from crud.cleanings import cleanings_crud
from crud.evaluations import evaluations_crud


async def get_cleaner_by_id_from_path(
    cleaner_id: Annotated[UUID, Path()],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> CleanerInfo:
    if cleaner := await evaluations_crud.get_cleaner_info(
        session=session,
        user_id=cleaner_id,
    ):
        return cleaner

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Cleaning specialist not found",
    )


async def get_cleaner_info_with_cleanings(
    cleaner: Annotated[CleanerInfo, Depends(get_cleaner_by_id_from_path)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> CleanerInfo:
    cleanings = await cleanings_crud.get_all_cleanings(
        session=session,
        user_id=cleaner.user_id,
    )
    cleaner.cleanings = [CleaningPublic(**cl.as_dict()) for cl in cleanings]

    return cleaner
