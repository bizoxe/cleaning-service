from collections.abc import (
    Awaitable,
    Callable,
)
from typing import Any

import pytest
import pytest_asyncio
from fastapi import (
    FastAPI,
    status,
)
from httpx import AsyncClient
from sqlalchemy import insert

from api.api_v1.cleanings.models import Cleaning
from api.api_v1.cleanings.schemas import (
    CleaningCreate,
    CleaningInDB,
    CleaningPublic,
    CleaningType,
)
from api.api_v1.offers.schemas import (
    OfferCompleted,
    OfferPublic,
)
from auth.schemas import UserAuthSchema
from tests.database import session_manager

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="function")
async def create_cleaning_jobs(connection_test, create_fake_user) -> list[Cleaning]:
    cleanings = []
    for _ in range(1, 151):
        cleaning = CleaningCreate(
            name="window cleaning",
            price=120,
            description="test cleaning job",
            cleaning_type=CleaningType("spot clean"),
        )
        cleaning_in_db = CleaningInDB(
            owner=create_fake_user.id,
            **cleaning.model_dump(),
        )
        cleanings.append(cleaning_in_db)
    async with session_manager.session() as session:
        instances = [{**obj.model_dump()} for obj in cleanings]
        result = await session.scalars(insert(Cleaning).returning(Cleaning).values(instances))
        await session.flush()
        await session.commit()

        return result.all()


class TestOffersRoutesUnauthorizedUser:

    async def test_create_offer_for_cleaning_owner(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await client.post(
            app.url_path_for(
                "offers:create-offer-for-cleaning-owner",
                cleaning_id=create_fake_cleaning.id,
            ),
            json={},
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_show_all_cleanings(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        response = await client.get(
            app.url_path_for("offers:show-all-cleanings"),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_show_offers_with_status_accepted(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        response = await client.get(
            app.url_path_for("offers:show-offers-with-status-accepted"),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_show_offer_by_cleaning_id(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await client.get(
            app.url_path_for(
                "offers:show-offer-by-cleaning-id",
                cleaning_id=create_fake_cleaning.id,
            ),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_show_all_self_offers(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        response = await client.get(
            app.url_path_for("offers:show-all-self-offers"),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_set_offer_to_completed_status(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await client.put(
            app.url_path_for(
                "offers:set-offer-to-completed-status",
                cleaning_id=create_fake_cleaning.id,
            ),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_delete_all_completed_offers(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        response = await client.delete(
            app.url_path_for("offers:delete-all-completed-offers"),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_delete_all_rejected_offers(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        response = await client.delete(
            app.url_path_for("offers:delete-all-rejected-offers"),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestOffersRoutesCleanerUser:

    async def test_create_offer_permission_denied(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        data = {
            "requested_date": None,
            "requested_time": None,
        }
        response = await authorized_client_cleaner.post(
            app.url_path_for(
                "offers:create-offer-for-cleaning-owner",
                cleaning_id=create_fake_cleaning.id,
            ),
            json=data,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_show_all_cleanings_permission_denied(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for("offers:show-all-cleanings"),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_show_offers_with_status_accepted_perm_denied(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for("offers:show-offers-with-status-accepted"),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_show_offer_by_cleaning_id_perm_denied(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for(
                "offers:show-offer-by-cleaning-id",
                cleaning_id=create_fake_cleaning.id,
            ),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_show_all_self_offers_perm_denied(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for("offers:show-all-self-offers"),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_set_offer_to_completed_status_perm_denied(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await authorized_client_cleaner.put(
            app.url_path_for(
                "offers:set-offer-to-completed-status",
                cleaning_id=create_fake_cleaning.id,
            ),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_all_completed_offers_perm_denied(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
    ) -> None:
        response = await authorized_client_cleaner.delete(
            app.url_path_for("offers:delete-all-completed-offers"),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_all_rejected_offers_perm_denied(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
    ) -> None:
        response = await authorized_client_cleaner.delete(
            app.url_path_for("offers:delete-all-rejected-offers"),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestOffersCreate:

    @pytest.mark.parametrize(
        "payload, status_code",
        [
            (
                {
                    "requested_date": "2025-03-13",
                    "requested_time": "10:00",
                },
                201,
            ),
            (
                {
                    "requested_date": None,
                    "requested_time": None,
                },
                201,
            ),
        ],
    )
    async def test_create_offer_for_cleaning_owner_valid_input(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_fake_customer_profile: UserAuthSchema,
        payload: dict[str, Any],
        status_code: int,
    ) -> None:
        response = await authorized_client_customer.post(
            app.url_path_for(
                "offers:create-offer-for-cleaning-owner",
                cleaning_id=create_fake_cleaning.id,
            ),
            json=payload,
        )
        resp_dict = response.json()
        offer_public_resp = OfferPublic(
            requested_date=resp_dict.pop("requested_date", None),
            requested_time=resp_dict.pop("requested_time", None),
            **resp_dict,
        )
        assert offer_public_resp.offerer_id == create_fake_customer_profile.id
        assert offer_public_resp.cleaning_id == create_fake_cleaning.id
        assert offer_public_resp.status == "pending"
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.parametrize(
        "payload, status_code",
        [
            (
                {
                    "requested_date": "2025-02-03",
                    "requested_time": "22",
                },
                422,
            ),
            (
                {
                    "requested_date": "2025",
                    "requested_time": "12:00",
                },
                422,
            ),
        ],
    )
    async def test_create_offer_for_cleaning_owner_invalid_input(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        payload: dict[str, Any],
        status_code: int,
    ) -> None:
        response = await authorized_client_customer.post(
            app.url_path_for(
                "offers:create-offer-for-cleaning-owner",
                cleaning_id=create_fake_cleaning.id,
            ),
            json=payload,
        )
        assert response.status_code == status_code

    async def test_create_offer_for_cleaning_owner_without_profile(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await authorized_client.post(
            app.url_path_for(
                "offers:create-offer-for-cleaning-owner",
                cleaning_id=create_fake_cleaning.id,
            ),
            json={},
        )
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT

    async def test_create_offer_more_than_one_cleaning_job(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_customer.post(
            app.url_path_for(
                "offers:create-offer-for-cleaning-owner",
                cleaning_id=create_fake_cleaning.id,
            ),
            json={
                "requested_date": "2025-02-03",
                "requested_time": "12:00",
            },
        )
        msg = response.json().get("detail")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert msg == "Users aren't allowed create more than one offer for a cleaning job"

    async def test_create_offer_cleaning_not_found(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
    ) -> None:
        response = await authorized_client_customer.post(
            app.url_path_for(
                "offers:create-offer-for-cleaning-owner",
                cleaning_id=99,
            ),
            json={
                "requested_date": "2025-02-03",
                "requested_time": "12:00",
            },
        )
        msg = response.json().get("detail")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert msg == "No cleaning found with that id"


class TestShowAllCleanings:

    @pytest.mark.parametrize(
        "max_results, status_code",
        [
            (
                80,
                200,
            ),
            (
                100,
                200,
            ),
        ],
    )
    async def test_show_all_cleanings(
        self,
        authorized_client_customer: AsyncClient,
        create_cleaning_jobs: list[Cleaning],
        max_results: int,
        status_code: int,
    ) -> None:
        response = await authorized_client_customer.get(
            f"/api/v1/offers/show-cleanings?{max_results=}&descending=false"
        )
        assert response.json().get("count") == max_results
        count_items = response.json().get("items")
        assert len(count_items) == max_results
        assert response.status_code == status_code

    async def test_show_all_cleanings_check_cursor(
        self,
        authorized_client_customer: AsyncClient,
        create_cleaning_jobs: list[Cleaning],
    ) -> None:
        response = await authorized_client_customer.get(
            "/api/v1/offers/show-cleanings?max_results=80&descending=false"
        )
        assert response.json()["previous_cursor"] is None
        cursor = response.json().get("next_cursor")
        residue_elements_in_sequence = len(create_cleaning_jobs) - 80
        response_cursor = await authorized_client_customer.get(
            f"/api/v1/offers/show-cleanings?max_results=100&{cursor=}&descending=false"
        )
        assert response_cursor.json()["next_cursor"] is None
        assert response_cursor.json().get("count") == residue_elements_in_sequence
        assert response_cursor.json().get("previous_cursor") != ""


class TestShowSelfOffers:

    async def test_show_offers_with_status_accepted(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        change_offer_status: Callable[[str], Awaitable[OfferPublic]],
    ) -> None:
        set_offer_status = await change_offer_status("accepted")
        response = await authorized_client_customer.get(app.url_path_for("offers:show-offers-with-status-accepted"))
        resp_offer_list = [OfferPublic(**resp) for resp in response.json()]
        assert len(resp_offer_list) == 1
        assert resp_offer_list[0] == set_offer_status
        assert response.status_code == status.HTTP_200_OK

    async def test_show_offers_with_status_accepted_not_found(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_customer.get(app.url_path_for("offers:show-offers-with-status-accepted"))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_show_offer_by_cleaning_id(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_customer.get(
            app.url_path_for(
                "offers:show-offer-by-cleaning-id",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        resp_offer_public = OfferPublic(**response.json())
        assert resp_offer_public.offerer_id == create_offer_in_db.offerer_id
        assert resp_offer_public.cleaning_id == create_fake_cleaning.id
        assert resp_offer_public.status == "pending"

    async def test_show_offer_by_cleaning_id_not_found(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await authorized_client_customer.get(
            app.url_path_for(
                "offers:show-offer-by-cleaning-id",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        msg = response.json().get("detail")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert msg == "You don't have an offer for this cleaning job"

    async def test_show_all_self_offers(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_customer.get(app.url_path_for("offers:show-all-self-offers"))
        offers_list = [OfferPublic(**of) for of in response.json()]
        assert len(offers_list) == 1
        assert response.status_code == status.HTTP_200_OK

    async def test_show_all_self_offers_empty_list(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
    ) -> None:
        response = await authorized_client_customer.get(app.url_path_for("offers:show-all-self-offers"))
        offers_list = [OfferPublic(**of) for of in response.json()]
        assert len(offers_list) == 0
        assert response.status_code == status.HTTP_200_OK


class TestSetOfferCompletedStatus:

    async def test_set_offer_to_completed_status(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        change_offer_status: Callable[[str], Awaitable[OfferPublic]],
    ) -> None:
        set_offer_status = await change_offer_status("accepted")  # noqa F841
        response = await authorized_client_customer.put(
            app.url_path_for(
                "offers:set-offer-to-completed-status",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        resp_offer_completed = OfferCompleted(**response.json())
        assert resp_offer_completed.cleaner_id == create_fake_cleaning.owner
        assert resp_offer_completed.status == "completed"
        assert response.status_code == status.HTTP_200_OK

    async def test_set_offer_to_completed_status_invalid_status(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_customer.put(
            app.url_path_for(
                "offers:set-offer-to-completed-status",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_set_offer_to_completed_status_offer_not_found(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await authorized_client_customer.put(
            app.url_path_for(
                "offers:set-offer-to-completed-status",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        msg = response.json().get("detail")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert msg == "Offer not found"


class TestOffersDeleteRoutes:

    async def test_delete_all_completed_offers(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        change_offer_status: Callable[[str], Awaitable[OfferPublic]],
    ) -> None:
        set_status = await change_offer_status("completed")  # noqa F841
        response = await authorized_client_customer.delete(app.url_path_for("offers:delete-all-completed-offers"))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_all_completed_offers_invalid_status(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_customer.delete(app.url_path_for("offers:delete-all-completed-offers"))
        msg = response.json().get("detail")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert msg == "You don't have any offers with status 'completed' to remove yet"

    async def test_delete_all_completed_offers_without_created_offers(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
    ) -> None:
        response = await authorized_client_customer.delete(app.url_path_for("offers:delete-all-completed-offers"))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_delete_all_rejected_offers(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        change_offer_status: Callable[[str], Awaitable[OfferPublic]],
    ) -> None:
        set_status = await change_offer_status("rejected")  # noqa F841
        response = await authorized_client_customer.delete(app.url_path_for("offers:delete-all-rejected-offers"))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_all_rejected_offers_invalid_status(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_offer_in_db: OfferPublic,
    ) -> None:
        response = await authorized_client_customer.delete(app.url_path_for("offers:delete-all-rejected-offers"))
        msg = response.json().get("detail")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert msg == "You don't have any offers with status 'rejected' to remove yet"

    async def test_delete_all_rejected_offers_without_created_offers(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
    ) -> None:
        response = await authorized_client_customer.delete(app.url_path_for("offers:delete-all-rejected-offers"))
        assert response.status_code == status.HTTP_400_BAD_REQUEST
