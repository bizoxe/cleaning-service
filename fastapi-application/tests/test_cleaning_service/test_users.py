from collections.abc import (
    Awaitable,
    Callable,
)
from uuid import UUID

import pytest
from fastapi import (
    FastAPI,
    status,
)
from httpx import AsyncClient
from sqlalchemy import select

from api.api_v1.profiles.models import Profile
from api.api_v1.users.schemas import UserPublic
from auth.schemas import (
    UserAuthProfile,
    UserAuthSchema,
)
from tests.database import session_manager

pytestmark = pytest.mark.asyncio


@pytest.fixture
def get_profile_by_user_id(connection_test) -> Callable[[UUID], Awaitable[UserAuthProfile]]:
    async def _get_profile_by_user_id(user_id: UUID) -> UserAuthProfile:
        async with session_manager.session() as session:
            profile = await session.scalar(
                select(Profile).filter_by(user_id=user_id),
            )
            return UserAuthProfile(**profile.as_dict())

    return _get_profile_by_user_id


class TestUserResetPwd:

    async def test_reset_user_password(
        self,
        app: FastAPI,
        client: AsyncClient,
        authorized_client: AsyncClient,
    ) -> None:
        data = {
            "password": "secretpwdL1@",
            "confirm_password": "secretpwdL1@",
        }
        data_login = {
            "username": "fakeuser@gmail.com",
            "password": data["password"],
        }
        response = await authorized_client.patch(
            app.url_path_for("users:reset-user-password"),
            json=data,
        )
        assert response.status_code == status.HTTP_200_OK
        resp_login = await client.post(
            app.url_path_for("auth:auth-user-issue-jwt"),
            data=data_login,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp_login.json()["access_token"] != ""
        assert resp_login.json()["refresh_token"] != ""
        assert resp_login.status_code == status.HTTP_200_OK

    async def test_reset_password_unauthorized_user(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        response = await client.patch(
            app.url_path_for("users:reset-user-password"),
            json={
                "password": "secretpwdL1@",
                "confirm_password": "secretpwdL1@",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateUserEmail:

    async def test_update_self_email(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
    ) -> None:
        response = await authorized_client.patch(
            app.url_path_for("users:update-self-email"),
            json={"email": "teddy@example.com"},
        )
        resp_user_public = UserPublic(**response.json())
        assert resp_user_public.email == "teddy@example.com"
        assert response.status_code == status.HTTP_200_OK

    async def test_update_self_email_has_profile(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        get_profile_by_user_id: Callable[[UUID], Awaitable[UserAuthProfile]],
        create_fake_customer_profile: UserAuthSchema,
    ) -> None:
        response = await authorized_client_customer.patch(
            app.url_path_for("users:update-self-email"),
            json={"email": "teddy@example.com"},
        )
        user_publ_resp = UserPublic(**response.json())
        user_profile = await get_profile_by_user_id(create_fake_customer_profile.id)
        assert user_publ_resp.email == "teddy@example.com"
        assert user_profile.email == user_publ_resp.email
        assert user_publ_resp.id == user_profile.user_id
        assert response.status_code == status.HTTP_200_OK

    async def test_update_email_not_unique_email(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        create_fake_user: UserAuthSchema,
    ) -> None:
        response = await authorized_client.patch(
            app.url_path_for("users:update-self-email"),
            json={"email": create_fake_user.email},
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    async def test_update_email_unauthorized_user(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        response = await client.patch(
            app.url_path_for("users:update-self-email"),
            json={"email": "teddy@example.com"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
