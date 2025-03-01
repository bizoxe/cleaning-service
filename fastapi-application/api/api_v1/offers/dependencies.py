from collections.abc import (
    Awaitable,
    Callable,
)
from typing import Annotated
from uuid import UUID

from fastapi import (
    Depends,
    HTTPException,
    Path,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.cleanings.dependencies import get_one_cleaning
from api.api_v1.cleanings.models import Cleaning
from api.api_v1.offers.schemas import OfferPublic
from auth.dependencies import UserProfilePermissionGetter
from auth.schemas import UserAuthSchema
from core.models import db_helper
from crud.offers import offers_crud


async def get_offer_from_user_by_user_id(
    offerer_id: Annotated[UUID, Path()],
    cleaning: Annotated[Cleaning, Depends(get_one_cleaning)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> OfferPublic:
    if offer := await offers_crud.get_user_offer(
        session=session,
        user_id=offerer_id,
        cleaning_id=cleaning.id,
    ):
        oferrer_info = await offers_crud.get_user_info_from_profile(
            session=session,
            user_id=offerer_id,
        )
        offer_public = OfferPublic(offerer=oferrer_info, **offer.as_dict())
        return offer_public

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Offer not found",
    )


def check_offer_status(
    offer_status: str,
) -> Callable[[UserAuthSchema, int, AsyncSession], Awaitable[OfferPublic]]:
    async def get_offer(
        user_auth: Annotated[UserAuthSchema, Depends(UserProfilePermissionGetter("customer"))],
        cleaning_id: Annotated[int, Path(ge=1)],
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    ) -> OfferPublic:
        if offer := await offers_crud.get_user_offer(
            session=session,
            user_id=user_auth.id,
            cleaning_id=cleaning_id,
        ):
            if offer.status != offer_status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Offer has a status of {offer.status!r}, a status of {offer_status!r} is required",
                )
            return OfferPublic(**offer.as_dict())

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found",
        )

    return get_offer


def check_offers_with_a_specific_status_to_delete(
    offer_status: str,
) -> Callable[[UserAuthSchema, AsyncSession], Awaitable[UserAuthSchema]]:
    async def get_offers(
        user_auth: Annotated[UserAuthSchema, Depends(UserProfilePermissionGetter("customer"))],
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    ) -> UserAuthSchema:
        if offers := await offers_crud.get_offers_with_status(  # noqa: F841
            session=session,
            user_id=user_auth.id,
            status=offer_status,
        ):
            return user_auth

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You don't have any offers with status {offer_status!r} to remove yet",
        )

    return get_offers
