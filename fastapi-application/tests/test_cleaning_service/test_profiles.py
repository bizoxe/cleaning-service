from typing import Any

import pytest
from fastapi import (
    FastAPI,
    status,
)
from httpx import AsyncClient

from api.api_v1.profiles.schemas import (
    ProfileCreate,
    ProfilePublic,
    ProfileUpdate,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def create_profile() -> ProfileCreate:

    return ProfileCreate(
        first_name="Dima",
        last_name="Matveev",
        phone_number="+375(29)999-09-09",
        bio="fake bio",
        avatar="https://example.com/",
    )


@pytest.fixture
def create_profile_update() -> ProfileUpdate:

    return ProfileUpdate(
        first_name="updatedname",
        last_name="updatedname",
        phone_number="+375(29)999-09-09",
        bio="about me",
        avatar="https://example.com/",
    )


class TestProfileRoutesUnauthorisedUser:
    async def test_profile_routes(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        headers = {**client.headers, "Authorization": "Bearer"}
        resp = await client.post(
            app.url_path_for("profiles:create-profile-for-user-auth"),
            json={},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        resp = await client.post(
            app.url_path_for("profiles:get-user-auth-self-profile"),
            json={},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        resp = await client.post(
            app.url_path_for("profiles:update-user-auth-self-profile"),
            json={},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


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
                },
                201,
            ),
            (
                {
                    "first_name": "Elena",
                    "last_name": "Dolgorukaya",
                    "phone_number": "+375(25)999-09-09",
                    "bio": None,
                    "avatar": None,
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
        profile_create = ProfileCreate(**payload).model_dump()
        profile = ProfilePublic(**resp.json()).model_dump()
        assert profile_create == profile
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
        assert (
            msg
            == "Value error, Only letters are allowed. Do not use special characters or numbers"
        )
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
        assert (
            msg
            == "Value error, Allowable format of mobile phone numbers without spaces: +375(xx)xxx-xx-xx"
        )
        assert resp.status_code == status_code

    async def test_create_profile_for_user_auth_exists(
        self,
        app: FastAPI,
        create_fake_profile: ProfilePublic,
        authorized_client: AsyncClient,
        create_profile: ProfileCreate,
    ) -> None:
        resp = await authorized_client.post(
            app.url_path_for("profiles:create-profile-for-user-auth"),
            json=create_profile.model_dump(),
        )
        assert resp.status_code == status.HTTP_409_CONFLICT


class TestGetSelfProfile:
    async def test_get_user_auth_self_profile(
        self,
        app: FastAPI,
        create_fake_profile: ProfilePublic,
        authorized_client: AsyncClient,
    ) -> None:
        resp = await authorized_client.get(
            app.url_path_for("profiles:get-user-auth-self-profile")
        )
        assert create_fake_profile == ProfilePublic(**resp.json())
        assert resp.status_code == status.HTTP_200_OK

    async def test_get_user_auth_self_profile_not_exists(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
    ) -> None:
        resp = await authorized_client.get(
            app.url_path_for("profiles:get-user-auth-self-profile")
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestProfileUpdate:
    async def test_update_user_auth_self_profile(
        self,
        app: FastAPI,
        create_fake_profile: ProfilePublic,
        authorized_client: AsyncClient,
        create_profile_update: ProfileUpdate,
    ) -> None:
        to_update = create_profile_update.model_dump()
        resp = await authorized_client.put(
            app.url_path_for("profiles:update-user-auth-self-profile"),
            json=to_update,
        )
        updated_profile = ProfilePublic(**resp.json())
        assert updated_profile == ProfilePublic(**to_update)
        assert resp.status_code == status.HTTP_200_OK

    async def test_update_user_auth_self_profile_not_exists(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        create_profile_update: ProfileUpdate,
    ) -> None:
        to_update = create_profile_update.model_dump()
        resp = await authorized_client.put(
            app.url_path_for("profiles:update-user-auth-self-profile"),
            json=to_update,
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
