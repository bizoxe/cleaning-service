from typing import Annotated

from fastapi import (
    Depends,
    HTTPException,
    Path,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.cleanings.models import Cleaning
from core.models import db_helper
from crud.cleanings import cleanings_crud


async def get_one_cleaning(
    cleaning_id: Annotated[int, Path(ge=1)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Cleaning:
    """
    Gets cleaning by ID from path.
    """
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
