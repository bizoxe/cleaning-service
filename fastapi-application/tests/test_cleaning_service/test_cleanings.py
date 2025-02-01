from typing import Any

import pytest
import pytest_asyncio
from fastapi import (
    FastAPI,
    status,
)
from httpx import AsyncClient
from sqlalchemy import insert

from tests.database import session_manager
from auth.schemas import UserAuthSchema
from api.api_v1.cleanings.models import Cleaning
from api.api_v1.cleanings.schemas import (
    CleaningCreate,
    CleaningInDB,
    CleaningPublic,
)
from api.api_v1.users.schemas import UserPublic

pytestmark = pytest.mark.asyncio


@pytest.fixture
def create_cleaning() -> CleaningCreate:
    return CleaningCreate(
        name="test cleaning",
        price=20.0,
        description="cleaning for test",
        cleaning_type="spot clean",
    )


@pytest.fixture
def create_cleaning_2() -> CleaningCreate:
    return CleaningCreate(
        name="test",
        price=20.0,
        description="test",
        cleaning_type="full clean",
    )


@pytest_asyncio.fixture(scope="function")
async def create_fake_cleaning(
    create_fake_user: UserAuthSchema,
    create_cleaning: CleaningCreate,
) -> CleaningPublic:
    async with session_manager.session() as session:
        cleaning_schema = create_cleaning.model_dump()
        cleaning_in_db = CleaningInDB(owner=create_fake_user.id, **cleaning_schema)
        cleaning = Cleaning(**cleaning_in_db.model_dump())
        session.add(cleaning)
        await session.commit()
        await session.refresh(cleaning)

        return CleaningPublic(**cleaning.as_dict())


@pytest_asyncio.fixture(scope="function")
async def create_fake_multiple_cleanings(
    create_fake_user: UserAuthSchema,
    create_cleaning: CleaningCreate,
    create_cleaning_2: CleaningCreate,
) -> list[Cleaning]:
    cleaning_schemas = [create_cleaning.model_dump(), create_cleaning_2.model_dump()]
    cleanings_in_db = [
        CleaningInDB(owner=create_fake_user.id, **cleaning)
        for cleaning in cleaning_schemas
    ]
    instances = [{**obj.model_dump()} for obj in cleanings_in_db]
    async with session_manager.session() as session:
        results = await session.scalars(
            insert(Cleaning).returning(Cleaning).values(instances)
        )
        await session.flush()
        await session.commit()

        return results.all()


class TestCleaningsRoutesUnauthorizedUser:

    async def test_create_new_cleaning_route(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        headers = {**client.headers, "Authorization": "Bearer"}
        response = await client.post(
            app.url_path_for("cleanings:create-cleaning"),
            json={},
            headers=headers,
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


class TestCleaningsCreate:

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
        authorized_client: AsyncClient,
        payload: dict[str, Any],
        status_code: int,
    ) -> None:
        response = await authorized_client.post(
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
        authorized_client: AsyncClient,
        payload: dict[str, Any],
        status_code: int,
    ) -> None:
        response = await authorized_client.post(
            app.url_path_for("cleanings:create-cleaning"),
            json=payload,
        )
        assert response.status_code == status_code


class TestCleaningsGetByID:

    async def test_get_cleaning_by_id(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
        create_fake_user: UserAuthSchema,
    ) -> None:
        response = await authorized_client.get(
            app.url_path_for(
                "cleanings:get-cleaning-by-id",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        cleaning_resp = CleaningPublic(**response.json())
        create_fake_cleaning.owner = UserPublic(**create_fake_user.model_dump())
        assert cleaning_resp == create_fake_cleaning
        assert response.status_code == status.HTTP_200_OK

    async def test_get_cleaning_by_id_not_found(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
    ) -> None:
        response = await authorized_client.get(
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
        authorized_client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        cleaning_schema = CleaningCreate(
            name="test",
            price=20.0,
            description=None,
            cleaning_type="full clean",
        )
        response = await authorized_client.put(
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
        authorized_client: AsyncClient,
    ) -> None:
        response = await authorized_client.put(
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
        authorized_client: AsyncClient,
        create_fake_cleaning: CleaningPublic,
    ) -> None:
        response = await authorized_client.delete(
            app.url_path_for(
                "cleanings:delete-cleaning",
                cleaning_id=create_fake_cleaning.id,
            )
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_cleaning_not_found(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
    ) -> None:
        response = await authorized_client.delete(
            app.url_path_for("cleanings:delete-cleaning", cleaning_id=99)
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCleaningsGetAllCleanings:

    async def test_get_user_all_cleanings(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        create_fake_multiple_cleanings: list[Cleaning],
    ) -> None:
        response = await authorized_client.get(
            app.url_path_for("cleanings:get-all-cleanings")
        )
        cleaning_schemas = [
            CleaningPublic(**cl.as_dict()) for cl in create_fake_multiple_cleanings
        ]
        cleaning_resp = [CleaningPublic(**rs) for rs in response.json()]
        assert cleaning_resp == cleaning_schemas
        assert len(response.json()) == len(create_fake_multiple_cleanings)
        assert response.status_code == status.HTTP_200_OK
