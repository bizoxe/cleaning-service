from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.cleanings.dependencies import get_one_cleaning
from api.api_v1.cleanings.models import Cleaning
from api.api_v1.offers.dependencies import get_offer_from_user_by_user_id
from api.api_v1.offers.schemas import (
    OfferPublic,
    OfferUpdate,
)
from auth.dependencies import UserProfilePermissionGetter
from core.models import db_helper
from crud.offers import offers_crud

router = APIRouter(
    tags=["Offers for cleaning owners"],
    dependencies=[Depends(UserProfilePermissionGetter("cleaner"))],
)


@router.get(
    "",
    response_model=list[OfferPublic],
    response_model_exclude_none=True,
    name="offers-cleanings:show-offers-for-one-cleaning",
    summary="show all offers for a specific cleaning job",
)
async def show_offers_for_cleaning_owner_by_cleaning_id(
    cleaning: Annotated[Cleaning, Depends(get_one_cleaning)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=30),
) -> list[OfferPublic]:
    offers = await offers_crud.get_offers_for_cleaning_owner(
        session=session,
        cleaning_id=cleaning.id,
        offset=skip,
        limit=limit,
    )
    return [OfferPublic(**offer.as_dict()) for offer in offers]


@router.get(
    "/{offerer_id}/info",
    name="offers-cleanings:show-offer-info",
    response_model=OfferPublic,
    response_model_exclude_none=True,
    summary="show information about the offer for cleaning owner",
)
async def show_offer_info(
    offer: Annotated[OfferPublic, Depends(get_offer_from_user_by_user_id)],
) -> OfferPublic:

    return offer


@router.put(
    "/{offerer_id}/accept",
    response_model=OfferPublic,
    response_model_exclude_none=True,
    name="offers-cleanings:cleaning-owner-accept-offer",
    summary="cleaning owner accepts the offer",
)
async def cleaning_owner_accept_offer(
    offer: Annotated[OfferPublic, Depends(get_offer_from_user_by_user_id)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> OfferPublic:
    if offer.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users can only accept offers in a pending status",
        )

    updated_offer = await offers_crud.update_offer_for_cleaning_owner(
        session=session,
        offer=offer,
        offer_update=OfferUpdate(status="accepted"),
    )

    return OfferPublic(offerer=offer.offerer, **updated_offer.as_dict())


@router.put(
    "/{offerer_id}/cancel",
    response_model=OfferPublic,
    response_model_exclude_none=True,
    name="offers-cleanings:cleaning-owner-cancel-offer",
    summary="cleaning owner cancels the offer",
)
async def cleaning_owner_cancel_offer(
    offer: Annotated[OfferPublic, Depends(get_offer_from_user_by_user_id)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> OfferPublic:
    if offer.status != "accepted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users can only cancel offers in the 'accepted' status",
        )

    canceled_offer = await offers_crud.update_offer_for_cleaning_owner(
        session=session,
        offer=offer,
        offer_update=OfferUpdate(status="rejected"),
    )

    return OfferPublic(offerer=offer.offerer, **canceled_offer.as_dict())


@router.put(
    "/{offerer_id}/reject",
    response_model=OfferPublic,
    response_model_exclude_none=True,
    name="offers-cleanings:cleaning-owner-reject-offer",
    summary="cleaning owner rejects the offer",
)
async def cleaning_owner_reject_offer(
    offer: Annotated[OfferPublic, Depends(get_offer_from_user_by_user_id)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> OfferPublic:
    if offer.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users can only reject offers that are in a pending status",
        )

    rejected_offer = await offers_crud.update_offer_for_cleaning_owner(
        session=session,
        offer=offer,
        offer_update=OfferUpdate(status="rejected"),
    )

    return OfferPublic(offerer=offer.offerer, **rejected_offer.as_dict())
