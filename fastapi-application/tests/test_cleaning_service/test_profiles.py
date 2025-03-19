from typing import Any

import pytest
import pytest_asyncio
from fastapi import (
    FastAPI,
    status,
)
from httpx import AsyncClient
from sqlalchemy import select

from api.api_v1.profiles.models import Profile
from api.api_v1.profiles.schemas import (
    MemberType,
    ProfileCreate,
    ProfilePublic,
    ProfileUpdate,
)
from auth.schemas import UserAuthSchema
from tests.database import session_manager

pytestmark = pytest.mark.asyncio


@pytest.fixture
def create_profile() -> ProfileCreate:

    return ProfileCreate(
        first_name="Dima",
        last_name="Matveev",
        phone_number="+375(29)999-09-09",
        bio="fake bio info",
        avatar="https://example.com/",
        register_as=MemberType("customer"),
    )


@pytest.fixture
def create_profile_to_update() -> ProfileUpdate:

    return ProfileUpdate(
        first_name="Updatedname",
        last_name="Updatedsurname",
        phone_number="+375(25)999-09-09",
        bio="updated about me info",
        avatar="https://example.com/",
    )


@pytest_asyncio.fixture(scope="function")
async def get_customer_profile(
    create_fake_customer_profile: UserAuthSchema,
) -> ProfilePublic:
    async with session_manager.session() as session:
        profile = await session.scalar(
            select(Profile).filter_by(
                user_id=create_fake_customer_profile.id,
            )
        )

        return ProfilePublic(**profile.as_dict())


@pytest_asyncio.fixture(scope="function")
async def get_cleaner_profile(
    create_fake_cleaner_profile: UserAuthSchema,
) -> ProfilePublic:
    async with session_manager.session() as session:
        profile = await session.scalar(
            select(Profile).filter_by(
                user_id=create_fake_cleaner_profile.id,
            )
        )

        return ProfilePublic(**profile.as_dict())


class TestProfileRoutesUnauthorisedUser:
    async def test_create_profile_for_user_auth(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_profile: ProfileCreate,
    ) -> None:
        data = create_profile.model_dump()
        data["avatar"] = str(data["avatar"])
        resp_prof_create = await client.post(
            app.url_path_for("profiles:create-profile-for-user-auth"),
            json=data,
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert resp_prof_create.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_user_auth_self_profile(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        resp_self_profile = await client.get(
            app.url_path_for("profiles:get-user-auth-self-profile"),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert resp_self_profile.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_update_user_auth_self_profile(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_profile_to_update: ProfileUpdate,
    ) -> None:
        resp_update_prof = await client.put(
            app.url_path_for("profiles:update-user-auth-self-profile"),
            json=create_profile_to_update.model_dump(),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert resp_update_prof.status_code == status.HTTP_401_UNAUTHORIZED


class TestProfilesCreate:

    @pytest.mark.parametrize(
        "payload, status_code",
        [
            (
                {
                    "first_name": "Elena",
                    "last_name": "Dolgorukaya",
                    "phone_number": "+375(25)999-09-09",
                    "bio": "info about me",
                    "avatar": "https://example.com/",
                    "register_as": "customer",
                },
                201,
            ),
            (
                {
                    "first_name": "Alex",
                    "last_name": "Matveev",
                    "phone_number": "+375(25)999-09-09",
                    "bio": None,
                    "avatar": None,
                    "register_as": "cleaner",
                },
                201,
            ),
        ],
    )
    async def test_create_profile_for_user_auth_valid_input(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        payload: dict[str, Any],
        status_code: int,
    ) -> None:
        resp = await authorized_client.post(
            app.url_path_for("profiles:create-profile-for-user-auth"),
            json=payload,
        )
        profile_create = ProfileCreate(**payload)
        profile = ProfilePublic(**resp.json())
        assert profile.first_name == profile_create.first_name
        assert profile.last_name == profile_create.last_name
        assert profile.phone_number == profile_create.phone_number
        assert profile.avatar == profile_create.avatar
        assert profile.bio == profile_create.bio
        assert profile.register_as == profile_create.register_as
        assert resp.status_code == status_code

    @pytest.mark.parametrize(
        "payload, status_code",
        [
            (
                {
                    "first_name": "Elena1",
                    "last_name": "Dolgorukaya",
                    "phone_number": "+375(25)999-09-09",
                    "bio": "info about me",
                    "avatar": "https://example.com/",
                    "register_as": "customer",
                },
                422,
            ),
            (
                {
                    "first_name": "Elena",
                    "last_name": "Dolgorukaya@",
                    "phone_number": "+375(25)999-09-09",
                    "bio": None,
                    "avatar": None,
                    "register_as": "cleaner",
                },
                422,
            ),
            (
                {
                    "first_name": "",
                    "last_name": "Dolgorukaya",
                    "phone_number": "+375(25)999-09-09",
                    "bio": None,
                    "avatar": None,
                    "register_as": "customer",
                },
                422,
            ),
        ],
    )
    async def test_create_profile_for_user_auth_invalid_names(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        payload: dict[str, Any],
        status_code: int,
    ) -> None:
        resp = await authorized_client.post(
            app.url_path_for("profiles:create-profile-for-user-auth"),
            json=payload,
        )
        msg = resp.json().get("detail")[0]["msg"]
        assert msg == "Value error, Only letters are allowed. Do not use special characters or numbers"
        assert resp.status_code == status_code

    @pytest.mark.parametrize(
        "payload, status_code",
        [
            (
                {
                    "first_name": "Elena",
                    "last_name": "Dolgorukaya",
                    "phone_number": "+375(2)999-09-09",
                    "bio": "info about me",
                    "avatar": "https://example.com/",
                    "register_as": "customer",
                },
                422,
            ),
            (
                {
                    "first_name": "Elena",
                    "last_name": "Dolgorukaya",
                    "phone_number": "+375(25)99-09-09",
                    "bio": None,
                    "avatar": None,
                    "register_as": "customer",
                },
                422,
            ),
        ],
    )
    async def test_create_profile_for_user_auth_invalid_phone_number(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        payload: dict[str, Any],
        status_code: int,
    ) -> None:
        resp = await authorized_client.post(
            app.url_path_for("profiles:create-profile-for-user-auth"),
            json=payload,
        )
        msg = resp.json().get("detail")[0]["msg"]
        assert msg == "Value error, Allowable format of mobile phone numbers without spaces: +375(xx)xxx-xx-xx"
        assert resp.status_code == status_code

    @pytest.mark.parametrize(
        "payload, status_code",
        [
            (
                {
                    "first_name": "Elena",
                    "last_name": "Dolgorukaya",
                    "phone_number": "+375(25)999-09-09",
                    "bio": "info about me",
                    "avatar": "https://example.com/",
                    "register_as": "teddy bear",
                },
                422,
            ),
            (
                {
                    "first_name": "Elena",
                    "last_name": "Dolgorukaya",
                    "phone_number": "+375(25)999-09-09",
                    "bio": "info about me",
                    "avatar": "https://example.com/",
                    "register_as": "pokemon",
                },
                422,
            ),
        ],
    )
    async def test_create_profile_for_user_auth_invalid_register_as(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        payload: dict[str, Any],
        status_code: int,
    ) -> None:
        response = await authorized_client.post(
            app.url_path_for("profiles:create-profile-for-user-auth"),
            json=payload,
        )
        msg = response.json().get("detail")[0]["msg"]
        assert response.status_code == status_code
        assert msg == "Input should be 'customer' or 'cleaner'"

    async def test_create_profile_for_user_auth_exists(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_profile: ProfileCreate,
    ) -> None:
        profile = create_profile.model_dump()
        profile["avatar"] = str(profile["avatar"])
        resp = await authorized_client_customer.post(
            app.url_path_for("profiles:create-profile-for-user-auth"),
            json=profile,
        )
        assert resp.status_code == status.HTTP_409_CONFLICT


class TestGetSelfProfile:
    async def test_get_user_auth_self_customer_profile(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        get_customer_profile: ProfilePublic,
    ) -> None:
        resp = await authorized_client_customer.get(app.url_path_for("profiles:get-user-auth-self-profile"))
        assert get_customer_profile == ProfilePublic(**resp.json())
        assert resp.json().get("register_as") == "customer"
        assert resp.status_code == status.HTTP_200_OK

    async def test_get_user_auth_self_cleaner_profile(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        get_cleaner_profile: ProfilePublic,
    ) -> None:
        resp = await authorized_client_cleaner.get(app.url_path_for("profiles:get-user-auth-self-profile"))
        assert get_cleaner_profile == ProfilePublic(**resp.json())
        assert resp.json().get("register_as") == "cleaner"
        assert resp.status_code == status.HTTP_200_OK

    async def test_get_user_auth_self_profile_not_exists(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
    ) -> None:
        resp = await authorized_client.get(app.url_path_for("profiles:get-user-auth-self-profile"))
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestProfileUpdate:
    async def test_update_user_auth_self_profile(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_profile_to_update: ProfileUpdate,
    ) -> None:
        resp = await authorized_client_customer.put(
            app.url_path_for("profiles:update-user-auth-self-profile"),
            json=create_profile_to_update.model_dump(),
        )
        updated_profile = ProfilePublic(**resp.json())
        assert updated_profile.first_name == create_profile_to_update.first_name
        assert updated_profile.last_name == create_profile_to_update.last_name
        assert updated_profile.phone_number == create_profile_to_update.phone_number
        assert updated_profile.bio == create_profile_to_update.bio
        assert updated_profile.avatar == create_profile_to_update.avatar
        assert resp.status_code == status.HTTP_200_OK

    async def test_update_user_auth_self_profile_not_exists(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        create_profile_to_update: ProfileUpdate,
    ) -> None:
        to_update = create_profile_to_update.model_dump()
        resp = await authorized_client.put(
            app.url_path_for("profiles:update-user-auth-self-profile"),
            json=to_update,
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
