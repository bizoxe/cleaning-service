from typing import Annotated

from fastapi import (
    Path,
    HTTPException,
    status,
    Depends,
)
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import db_helper
from crud.cleanings import cleanings_crud
from api.api_v1.cleanings.models import Cleaning


async def get_one_cleaning(
    cleaning_id: Annotated[int, Path(ge=1)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Cleaning:
    """
    Is used as a dependency for CRUD operations.
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
