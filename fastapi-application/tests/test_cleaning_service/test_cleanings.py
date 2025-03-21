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
from api.api_v1.users.schemas import UserPublic
from auth.schemas import UserAuthSchema
from tests.database import session_manager

pytestmark = pytest.mark.asyncio


@pytest.fixture
def create_cleaning_2() -> CleaningCreate:
    return CleaningCreate(
        name="flat cleaning",
        price=20.0,
        description="test flat cleaning",
        cleaning_type=CleaningType("full clean"),
    )


@pytest_asyncio.fixture(scope="function")
async def create_fake_multiple_cleanings(
    create_fake_cleaner_profile: UserAuthSchema,
    create_cleaning: CleaningCreate,
    create_cleaning_2: CleaningCreate,
) -> list[Cleaning]:
    cleaning_schemas = [create_cleaning.model_dump(), create_cleaning_2.model_dump()]
    cleanings_in_db = [CleaningInDB(owner=create_fake_cleaner_profile.id, **cleaning) for cleaning in cleaning_schemas]
    instances = [{**obj.model_dump()} for obj in cleanings_in_db]
    async with session_manager.session() as session:
        results = await session.scalars(insert(Cleaning).returning(Cleaning).values(instances))
        await session.flush()
        await session.commit()

        return results.all()


@pytest_asyncio.fixture(scope="function")
async def create_cl_to_check_permission(
    create_fake_user: UserAuthSchema,
    create_cleaning_2: CleaningCreate,
) -> Cleaning:
    async with session_manager.session() as session:
        cleaning_schema = create_cleaning_2.model_dump()
        cleaning_in_db = CleaningInDB(owner=create_fake_user.id, **cleaning_schema)
        cleaning = Cleaning(**cleaning_in_db.model_dump())
        session.add(cleaning)
        await session.commit()
        await session.refresh(cleaning)

        return cleaning


class TestCleaningsRoutesUnauthorizedUser:

    async def test_create_new_cleaning_route(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        response = await client.post(
            app.url_path_for("cleanings:create-cleaning"),
            json={},
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_cleaning_by_id_route(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await client.get(
            app.url_path_for(
                "cleanings:get-cleaning-by-id",
                cleaning_id=create_fake_cleaning.id,
            ),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_update_cleaning_route(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await client.put(
            app.url_path_for(
                "cleanings:update-cleaning",
                cleaning_id=create_fake_cleaning.id,
            ),
            json={},
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_delete_cleaning_route(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await client.delete(
            app.url_path_for(
                "cleanings:delete-cleaning",
                cleaning_id=create_fake_cleaning.id,
            ),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_user_all_cleanings_route(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        response = await client.get(
            app.url_path_for("cleanings:get-all-cleanings"),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCleaningsRoutesCustomerUser:
    async def test_create_new_cleaning(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_cleaning: CleaningCreate,
    ) -> None:
        response = await authorized_client_customer.post(
            app.url_path_for("cleanings:create-cleaning"),
            json=create_cleaning.model_dump(),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("detail") == "Only users registered as a cleaner can create cleanings"

    async def test_get_cleaning_by_id(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await authorized_client_customer.get(
            app.url_path_for(
                "cleanings:get-cleaning-by-id",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("detail") == "Access is only allowed to users registered as a 'cleaner'"

    async def test_update_cleaning(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_cleaning_2: CleaningCreate,
    ) -> None:
        response = await authorized_client_customer.put(
            app.url_path_for(
                "cleanings:update-cleaning",
                cleaning_id=create_fake_cleaning.id,
            ),
            json=create_cleaning_2.model_dump(),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("detail") == "Access is only allowed to users registered as a 'cleaner'"

    async def test_delete_cleaning(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await authorized_client_customer.delete(
            app.url_path_for(
                "cleanings:delete-cleaning",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("detail") == "Access is only allowed to users registered as a 'cleaner'"

    async def test_get_user_all_cleanings(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
    ) -> None:
        response = await authorized_client_customer.get(app.url_path_for("cleanings:get-all-cleanings"))
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("detail") == "Access is only allowed to users registered as a 'cleaner'"


class TestCleaningsCreate:
    async def test_create_new_cleaning_without_profile(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        create_cleaning: CleaningCreate,
    ) -> None:
        response = await authorized_client.post(
            app.url_path_for("cleanings:create-cleaning"),
            json=create_cleaning.model_dump(),
        )
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT

    @pytest.mark.parametrize(
        "payload, status_code",
        [
            (
                {
                    "name": "test",
                    "price": 12.0,
                    "description": "test description",
                    "cleaning_type": "dust up",
                },
                201,
            ),
            (
                {
                    "name": "test2",
                    "price": 12.0,
                    "description": None,
                    "cleaning_type": "full clean",
                },
                201,
            ),
        ],
    )
    async def test_create_new_cleaning_valid_input(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        payload: dict[str, Any],
        status_code: int,
    ) -> None:
        response = await authorized_client_cleaner.post(
            app.url_path_for("cleanings:create-cleaning"),
            json=payload,
        )
        cleaning_schema = CleaningCreate(**payload)
        cleaning_resp = CleaningPublic(**response.json())
        assert cleaning_resp.name == cleaning_schema.name
        assert cleaning_resp.price == cleaning_schema.price
        assert cleaning_resp.description == cleaning_schema.description
        assert cleaning_resp.cleaning_type == cleaning_schema.cleaning_type
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "payload, status_code",
        [
            (
                {
                    "name": "",
                    "price": 12.0,
                    "description": "test description",
                    "cleaning_type": "dust up",
                },
                422,
            ),
            (
                {
                    "name": "test",
                    "price": "some price",
                    "description": None,
                    "cleaning_type": "full clean",
                },
                422,
            ),
            (
                {
                    "name": "test",
                    "price": 12.0,
                    "description": None,
                    "cleaning_type": "bla bla",
                },
                422,
            ),
        ],
    )
    async def test_create_new_cleaning_invalid_input(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        payload: dict[str, Any],
        status_code: int,
    ) -> None:
        response = await authorized_client_cleaner.post(
            app.url_path_for("cleanings:create-cleaning"),
            json=payload,
        )
        assert response.status_code == status_code


class TestCleaningsGetByID:

    async def test_get_cleaning_by_id(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_fake_cleaner_profile: UserAuthSchema,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for(
                "cleanings:get-cleaning-by-id",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        cleaning_resp = CleaningPublic(**response.json())
        create_fake_cleaning.owner = UserPublic(
            **create_fake_cleaner_profile.model_dump(),
        )
        assert cleaning_resp == create_fake_cleaning
        assert response.status_code == status.HTTP_200_OK

    async def test_get_cleaning_by_id_not_found(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for(
                "cleanings:get-cleaning-by-id",
                cleaning_id=99,
            )
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCleaningsUpdateByID:

    async def test_update_cleaning(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        cleaning_schema = CleaningCreate(
            name="update cleaning test",
            price=20.0,
            description=None,
            cleaning_type=CleaningType("full clean"),
        )
        response = await authorized_client_cleaner.put(
            app.url_path_for(
                "cleanings:update-cleaning",
                cleaning_id=create_fake_cleaning.id,
            ),
            json=cleaning_schema.model_dump(),
        )
        cleaning_resp = CleaningPublic(**response.json())
        assert cleaning_resp.name == cleaning_schema.name
        assert cleaning_resp.price == cleaning_schema.price
        assert cleaning_resp.description == create_fake_cleaning.description
        assert cleaning_resp.cleaning_type == cleaning_schema.cleaning_type
        assert response.status_code == status.HTTP_200_OK

    async def test_update_cleaning_not_found(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
    ) -> None:
        response = await authorized_client_cleaner.put(
            app.url_path_for(
                "cleanings:update-cleaning",
                cleaning_id=99,
            ),
            json={},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCleaningsDeleteByID:

    async def test_delete_cleaning(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await authorized_client_cleaner.delete(
            app.url_path_for(
                "cleanings:delete-cleaning",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_cleaning_not_found(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
    ) -> None:
        response = await authorized_client_cleaner.delete(
            app.url_path_for(
                "cleanings:delete-cleaning",
                cleaning_id=99,
            )
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCleaningsGetAllCleanings:

    async def test_get_user_all_cleanings(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_multiple_cleanings: list[Cleaning],
    ) -> None:
        response = await authorized_client_cleaner.get(app.url_path_for("cleanings:get-all-cleanings"))
        cleaning_schemas = [CleaningPublic(**cl.as_dict()) for cl in create_fake_multiple_cleanings]
        cleaning_resp = [CleaningPublic(**rs) for rs in response.json()]
        assert cleaning_resp == cleaning_schemas
        assert len(response.json()) == len(create_fake_multiple_cleanings)
        assert response.status_code == status.HTTP_200_OK

    async def test_get_user_all_cleanings_empty_list(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
    ) -> None:
        response = await authorized_client_cleaner.get(app.url_path_for("cleanings:get-all-cleanings"))
        assert len(response.json()) == 0
        assert response.status_code == status.HTTP_200_OK


class TestCleanerHaveNoAccessToOtherCleanings:

    async def test_get_cleaning_by_id(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_cl_to_check_permission: Cleaning,
    ) -> None:
        response = await authorized_client_cleaner.get(
            app.url_path_for(
                "cleanings:get-cleaning-by-id",
                cleaning_id=create_cl_to_check_permission.id,
            )
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_cleaning(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_cl_to_check_permission: Cleaning,
    ) -> None:
        response = await authorized_client_cleaner.put(
            app.url_path_for(
                "cleanings:update-cleaning",
                cleaning_id=create_cl_to_check_permission.id,
            ),
            json={},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_cleaning(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_cl_to_check_permission: Cleaning,
    ) -> None:
        response = await authorized_client_cleaner.delete(
            app.url_path_for(
                "cleanings:delete-cleaning",
                cleaning_id=create_cl_to_check_permission.id,
            )
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
