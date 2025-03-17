from collections.abc import (
    Awaitable,
    Callable,
)
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import (
    FastAPI,
    status,
)
from httpx import AsyncClient
from sqlalchemy import select

from api.api_v1.cleanings.models import Cleaning
from api.api_v1.cleanings.schemas import (
    CleaningCreate,
    CleaningInDB,
    CleaningPublic,
    CleaningType,
)
from api.api_v1.offers.schemas import (
    OfferPublic,
    UserInfo,
)
from api.api_v1.profiles.models import Profile
from auth.schemas import (
    UserAuthProfile,
    UserAuthSchema,
)
from tests.database import session_manager

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="function")
async def create_default_cleaning(create_fake_user: UserAuthSchema) -> Cleaning:
    cleaning_schema = CleaningCreate(
        name="flat cleaning",
        price=120.0,
        description="flat cleaning for test",
        cleaning_type=CleaningType("full clean"),
    )
    async with session_manager.session() as session:
        cleaning_in_db = CleaningInDB(
            owner=create_fake_user.id,
            **cleaning_schema.model_dump(),
        )
        cleaning = Cleaning(**cleaning_in_db.model_dump())
        session.add(cleaning)
        await session.commit()
        await session.refresh(cleaning)

        return cleaning


@pytest_asyncio.fixture(scope="function")
async def get_offerer_profile_info(
    create_fake_customer_profile: UserAuthSchema,
) -> UserAuthProfile:
    async with session_manager.session() as session:
        user_profile = await session.scalar(select(Profile).filter_by(user_id=create_fake_customer_profile.id))

        return UserAuthProfile(**user_profile.as_dict())


class TestCleaningOffersRoutesUnauthorizedUser:

    async def test_show_offers_by_cleaning_id(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await client.get(
            app.url_path_for(
                "offers-cleanings:show-offers-for-one-cleaning",
                cleaning_id=create_fake_cleaning.id,
            ),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_show_offer_info(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await client.get(
            app.url_path_for(
                "offers-cleanings:show-offer-info",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=create_offer_in_db.offerer_id,
            ),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_cleaning_owner_accept_offer(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await client.put(
            app.url_path_for(
                "offers-cleanings:cleaning-owner-accept-offer",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=create_offer_in_db.offerer_id,
            ),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_cleaning_owner_cancel_offer(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await client.put(
            app.url_path_for(
                "offers-cleanings:cleaning-owner-cancel-offer",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=create_offer_in_db.offerer_id,
            ),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_cleaning_owner_reject_offer(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await client.put(
            app.url_path_for(
                "offers-cleanings:cleaning-owner-reject-offer",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=create_offer_in_db.offerer_id,
            ),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCleaningOffersRoutesCustomerUser:

    async def test_show_offers_by_cleaning_id(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_customer.get(
            app.url_path_for(
                "offers-cleanings:show-offers-for-one-cleaning",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_show_offer_info(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_customer.get(
            app.url_path_for(
                "offers-cleanings:show-offer-info",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=create_offer_in_db.offerer_id,
            )
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_cleaning_owner_accept_offer(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_customer.put(
            app.url_path_for(
                "offers-cleanings:cleaning-owner-accept-offer",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=create_offer_in_db.offerer_id,
            )
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_cleaning_owner_cancel_offer(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_customer.put(
            app.url_path_for(
                "offers-cleanings:cleaning-owner-cancel-offer",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=create_offer_in_db.offerer_id,
            )
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_cleaning_owner_reject_offer(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_customer.put(
            app.url_path_for(
                "offers-cleanings:cleaning-owner-reject-offer",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=create_offer_in_db.offerer_id,
            )
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestShowOffersForCleaningOwners:

    async def test_show_offers_by_cleaning_id(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for(
                "offers-cleanings:show-offers-for-one-cleaning",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        resp_offer_public_list = [OfferPublic(**of) for of in response.json()]
        assert len(resp_offer_public_list) == 1
        resp_offer_public = resp_offer_public_list[0]
        assert resp_offer_public.offerer_id == create_offer_in_db.offerer_id
        assert resp_offer_public.cleaning_id == create_fake_cleaning.id
        assert resp_offer_public.status == create_offer_in_db.status
        assert response.status_code == status.HTTP_200_OK

    async def test_show_offers_by_cleaning_id_empty_list(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for(
                "offers-cleanings:show-offers-for-one-cleaning",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        assert len(response.json()) == 0
        assert response.status_code == status.HTTP_200_OK

    async def test_show_offers_by_cleaning_id_perm_denied(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_default_cleaning: Cleaning,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for(
                "offers-cleanings:show-offers-for-one-cleaning",
                cleaning_id=create_default_cleaning.id,
            )
        )
        msg = response.json().get("detail")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert msg == "You are not the owner of this cleaning job"

    async def test_show_offers_by_cleaning_id_cleaning_not_found(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for(
                "offers-cleanings:show-offers-for-one-cleaning",
                cleaning_id=99,
            )
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_show_offer_info(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
        get_offerer_profile_info: UserAuthProfile,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for(
                "offers-cleanings:show-offer-info",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=create_offer_in_db.offerer_id,
            )
        )
        resp_offer_public = OfferPublic(**response.json())
        assert resp_offer_public.offerer_id == create_offer_in_db.offerer_id
        assert resp_offer_public.cleaning_id == create_fake_cleaning.id
        assert resp_offer_public.status == create_offer_in_db.status
        assert UserInfo(**get_offerer_profile_info.model_dump()) == resp_offer_public.offerer
        assert response.status_code == status.HTTP_200_OK

    async def test_show_offer_info_perm_denied(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_default_cleaning: Cleaning,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for(
                "offers-cleanings:show-offer-info",
                cleaning_id=create_default_cleaning.id,
                offerer_id=create_offer_in_db.offerer_id,
            )
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_show_offer_info_cleaning_not_found(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for(
                "offers-cleanings:show-offer-info",
                cleaning_id=99,
                offerer_id=create_offer_in_db.offerer_id,
            )
        )
        msg = response.json().get("detail")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert msg == "No cleaning found with that id"

    async def test_show_offer_info_offer_not_found(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for(
                "offers-cleanings:show-offer-info",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=uuid4(),
            )
        )
        msg = response.json().get("detail")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert msg == "Offer not found"


class TestCleaningOwnerAcceptOffer:

    async def test_cleaning_owner_accept_offer(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_cleaner.put(
            app.url_path_for(
                "offers-cleanings:cleaning-owner-accept-offer",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=create_offer_in_db.offerer_id,
            )
        )
        resp_offer_public = OfferPublic(**response.json())
        assert resp_offer_public.status == "accepted"
        assert response.status_code == status.HTTP_200_OK

    async def test_cleaning_owner_accept_offer_invalid_status(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        change_offer_status: Callable[[str], Awaitable[OfferPublic]],
    ) -> None:
        set_status = await change_offer_status("rejected")
        response = await authorized_client_cleaner.put(
            app.url_path_for(
                "offers-cleanings:cleaning-owner-accept-offer",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=set_status.offerer_id,
            )
        )
        msg = response.json().get("detail")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert msg == "Users can only accept offers in a pending status"


class TestCleaningOwnerCancelOffer:

    async def test_cleaning_owner_cancel_offer(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        change_offer_status: Callable[[str], Awaitable[OfferPublic]],
    ) -> None:
        set_status = await change_offer_status("accepted")
        response = await authorized_client_cleaner.put(
            app.url_path_for(
                "offers-cleanings:cleaning-owner-cancel-offer",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=set_status.offerer_id,
            )
        )
        resp_offer_public = OfferPublic(**response.json())
        assert resp_offer_public.status == "rejected"
        assert response.status_code == status.HTTP_200_OK

    async def test_cleaning_owner_cancel_offer_invalid_status(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_cleaner.put(
            app.url_path_for(
                "offers-cleanings:cleaning-owner-cancel-offer",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=create_offer_in_db.offerer_id,
            )
        )
        msg = response.json().get("detail")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert msg == "Users can only cancel offers in the 'accepted' status"


class TestCleaningOwnerRejectOffer:

    async def test_cleaning_owner_reject_offer(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_cleaner.put(
            app.url_path_for(
                "offers-cleanings:cleaning-owner-reject-offer",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=create_offer_in_db.offerer_id,
            )
        )
        resp_offer_public = OfferPublic(**response.json())
        assert resp_offer_public.status == "rejected"
        assert response.status_code == status.HTTP_200_OK

    async def test_cleaning_owner_reject_offer_invalid_status(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        change_offer_status: Callable[[str], Awaitable[OfferPublic]],
    ) -> None:
        set_status = await change_offer_status("accepted")
        response = await authorized_client_cleaner.put(
            app.url_path_for(
                "offers-cleanings:cleaning-owner-reject-offer",
                cleaning_id=create_fake_cleaning.id,
                offerer_id=set_status.offerer_id,
            )
        )
        msg = response.json().get("detail")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert msg == "Users can only reject offers that are in a pending status"
