from typing import (
    Annotated,
    Any,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.cleanings.dependencies import get_one_cleaning
from api.api_v1.cleanings.models import Cleaning
from api.api_v1.cleanings.schemas import CleaningPublic
from api.api_v1.offers.dependencies import (
    check_offer_status,
    check_offers_with_a_specific_status_to_delete,
)
from api.api_v1.offers.schemas import (
    CleaningInfo,
    ItemParamsCleaning,
    OfferCompleted,
    OfferCreate,
    OfferInDB,
    OfferPublic,
    OfferUpdate,
)
from api.api_v1.profiles.dependencies import (
    get_user_profile_or_http_exception,
)
from auth.dependencies import UserProfilePermissionGetter
from auth.schemas import (
    UserAuthProfile,
    UserAuthSchema,
)
from core.models import db_helper
from crud.offers import offers_crud
from utils.pagination.paginator import paginate
from utils.pagination.schemas import PaginatedResponse

router = APIRouter(
    tags=["Offers"],
)


@router.post(
    "/{cleaning_id}",
    response_model=OfferPublic,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    name="offers:create-offer-for-cleaning-owner",
    summary="creating an offer for a cleaning job",
)
async def create_offer_for_cleaning_owner(
    profile: Annotated[UserAuthProfile, Depends(get_user_profile_or_http_exception)],
    create_offer: OfferCreate,
    cleaning: Annotated[Cleaning, Depends(get_one_cleaning)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> OfferPublic:
    """
    Creates an offer for a cleaning job.

    If the user does not have a profile, the user is redirected to create a profile.
    User can only create one offer for a specific cleaning job.
    """
    if profile.register_as != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users registered as a customer can create offers",
        )

    offer_in_db = OfferInDB(
        offerer_id=profile.user_id,
        cleaning_id=cleaning.id,
        status="pending",
        requested_date=create_offer.requested_date,
        requested_time=create_offer.requested_time,
    )
    if created_offer := await offers_crud.create_new_offer(
        session=session,
        offer_schema=offer_in_db,
    ):
        cleaner_info = await offers_crud.get_user_info_from_profile(
            session=session,
            user_id=cleaning.owner,
        )
        created_offer.cleaning = CleaningInfo(
            cleaner=cleaner_info,
            **cleaning.as_dict(),
        )
        return created_offer

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Users aren't allowed create more than one offer for a cleaning job",
    )


@router.get(
    "/show-cleanings",
    response_model=PaginatedResponse[CleaningPublic],
    name="offers:show-all-cleanings",
    summary="show all cleaning jobs for offerer",
    dependencies=[Depends(UserProfilePermissionGetter("customer"))],
)
async def show_all_cleanings(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    params: ItemParamsCleaning = Depends(),
    max_results: int = Query(default=100, ge=1, le=100),
    cursor: str = Query(None),
) -> dict[str, Any]:
    """
    Gets all cleanings created by users registered as cleaners.
    """

    return await paginate(
        session=session,
        model=Cleaning,
        query=select(Cleaning),
        max_results=max_results,
        cursor=cursor,
        params=params,
    )


@router.get(
    "/accepted",
    response_model=list[OfferPublic],
    response_model_exclude_none=True,
    name="offers:show-offers-with-status-accepted",
    summary="show all offers for the offerer with accepted status",
)
async def show_offers_with_status_accepted(
    user_auth: Annotated[UserAuthSchema, Depends(UserProfilePermissionGetter("customer"))],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> list[OfferPublic]:
    if offers := await offers_crud.get_offers_with_status(
        session=session,
        user_id=user_auth.id,
        status="accepted",
    ):
        return offers

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="You do not have any offers with the status 'accepted' yet",
    )


@router.get(
    "/{cleaning_id}",
    response_model=OfferPublic,
    response_model_exclude_none=True,
    name="offers:show-offer-by-cleaning-id",
    summary="show one offer by cleaning ID",
)
async def show_offer_by_cleaning_id(
    user_auth: Annotated[UserAuthSchema, Depends(UserProfilePermissionGetter("customer"))],
    cleaning: Annotated[Cleaning, Depends(get_one_cleaning)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> OfferPublic:
    if offer := await offers_crud.get_user_offer(
        session=session,
        user_id=user_auth.id,
        cleaning_id=cleaning.id,
    ):
        cleaner_info = await offers_crud.get_user_info_from_profile(
            session=session,
            user_id=cleaning.owner,
        )
        offer_public = OfferPublic(**offer.as_dict())
        offer_public.cleaning = CleaningInfo(
            cleaner=cleaner_info,
            **cleaning.as_dict(),
        )
        return offer_public

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="You don't have an offer for this cleaning job",
    )


@router.get(
    "",
    response_model=list[OfferPublic],
    response_model_exclude_none=True,
    name="offers:show-all-self-offers",
    summary="show all offers created by the offerer",
)
async def show_all_self_offers(
    user_auth: Annotated[UserAuthSchema, Depends(UserProfilePermissionGetter("customer"))],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> list[OfferPublic]:
    offers = await offers_crud.get_all_offers_for_offerer(
        session=session,
        user_id=user_auth.id,
    )

    return [OfferPublic(**offer.as_dict()) for offer in offers]


@router.put(
    "/{cleaning_id}",
    name="offers:set-offer-to-completed-status",
    summary="set offer status completed",
)
async def set_offer_to_completed_status(
    cleaning: Annotated[Cleaning, Depends(get_one_cleaning)],
    offer: Annotated[OfferPublic, Depends(check_offer_status("accepted"))],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> OfferCompleted:
    to_update = OfferUpdate(status="completed")
    completed_offer = await offers_crud.update_offer_for_cleaning_owner(
        session=session,
        offer=offer,
        offer_update=to_update,
    )

    return OfferCompleted(cleaner_id=cleaning.owner, **completed_offer.as_dict())


@router.delete(
    "/completed",
    name="offers:delete-all-completed-offers",
    summary="deleting all completed offers for the offerer",
)
async def delete_all_completed_offers(
    user_auth: Annotated[
        UserAuthSchema,
        Depends(check_offers_with_a_specific_status_to_delete("completed")),
    ],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Response:
    await offers_crud.delete_offers_with_status(
        session=session,
        user_id=user_auth.id,
        status="completed",
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/rejected",
    name="offers:delete-all-rejected-offers",
    summary="deleting all rejected offers for the offerer",
)
async def delete_all_rejected_offers(
    user_auth: Annotated[
        UserAuthSchema,
        Depends(check_offers_with_a_specific_status_to_delete("rejected")),
    ],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Response:
    await offers_crud.delete_offers_with_status(
        session=session,
        user_id=user_auth.id,
        status="rejected",
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
