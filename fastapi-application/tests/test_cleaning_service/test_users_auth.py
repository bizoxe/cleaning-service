import re
from secrets import (
    token_hex,
    token_urlsafe,
)
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import (
    FastAPI,
    status,
)
from httpx import AsyncClient
from pytest_mock import MockFixture

from api.api_v1.users.jwt_helpers import create_refresh_token
from api.api_v1.users.schemas import UserCreate
from auth.schemas import (
    UserAuthInfo,
    UserAuthProfile,
    UserAuthSchema,
)
from utils.mailing.helpers import create_url_safe_token
from utils.mailing.messages import send_verify_email

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="function")
def authorized_client_refresh_jwt(
    client: AsyncClient,
    create_fake_user: UserAuthSchema,
) -> AsyncClient:
    refresh_token = create_refresh_token(user=create_fake_user)
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {refresh_token}",
    }

    return client


@pytest.fixture
def get_email_token_default() -> str:
    return create_url_safe_token("fakeuser@gmail.com")


@pytest.fixture
def get_email_token() -> str:
    return create_url_safe_token("dolgorukaya@gmail.com")


def replace_link_token(
    msg: str,
    token: str,
) -> str:
    link = re.search('(?<=href=")(.*?)(?=")', msg)
    link_without_token = link.group().split("/")[:-1]
    new_link = f'{"/".join(link_without_token)}/{token}'

    return new_link


@pytest_asyncio.fixture(scope="function")
async def mock_send_email(
    mocker: MockFixture,
    get_api_base_url: str,
    get_email_token_default: str,
) -> AsyncMock:
    mocker.patch("utils.mailing.send_email.aiosmtplib.send")
    mock_email_server = AsyncMock()
    token = get_email_token_default
    link = f"{get_api_base_url}api/v1/auth/verify-email/{token}"
    msg_html = f"""
        <h3>Confirm your email</h3>
        <p>Please click this <a href="{link}">link</a> to confirm your email</p>
        """
    mock_email_server.message = msg_html
    await send_verify_email("fakeuser@gmail.com")

    return mock_email_server


class TestUserRegistration:

    @pytest.mark.parametrize(
        "payload, status_code",
        [
            (
                {
                    "email": "elena@gmail.com",
                    "password": "elenastringL1@",
                    "confirm_password": "elenastringL1@",
                },
                201,
            ),
            (
                {
                    "email": "example@gmail.com",
                    "password": "secretpasswordD1$",
                    "confirm_password": "secretpasswordD1$",
                },
                201,
            ),
        ],
    )
    async def test_register_user_account_valid_input(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_role_and_permission,
        payload: dict[str, str],
        status_code: int,
    ) -> None:
        response = await client.post(
            app.url_path_for("auth:register-new-user"),
            json=payload,
        )
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "payload, status_code",
        [
            (
                {
                    "email": "",
                    "password": "secretpasswordD1$",
                    "confirm_password": "secretpasswordD1$",
                },
                422,
            ),
            (
                {
                    "email": "elena@#gmail.com",
                    "password": "secretpasswordD1$",
                    "confirm_password": "secretpasswordD1$",
                },
                422,
            ),
            (
                {
                    "email": "elena@#gmail",
                    "password": "secretpasswordD1$",
                    "confirm_password": "secretpasswordD1$",
                },
                422,
            ),
        ],
    )
    async def test_register_user_account_incorrect_email(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_role_and_permission,
        payload: dict[str, str],
        status_code: int,
    ) -> None:
        response = await client.post(
            app.url_path_for("auth:register-new-user"),
            json=payload,
        )
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "payload, status_code",
        [
            (
                {
                    "email": "elena@gmail.com",
                    "password": "",
                    "confirm_password": "",
                },
                422,
            ),
            (
                {
                    "email": "elena@gmail.com",
                    "password": "secret",
                    "confirm_password": "secret",
                },
                422,
            ),
        ],
    )
    async def test_register_user_account_invalid_pwd(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_role_and_permission,
        payload: dict[str, str],
        status_code: int,
    ) -> None:
        response = await client.post(
            app.url_path_for("auth:register-new-user"),
            json=payload,
        )
        assert response.status_code == status_code

    async def test_register_user_account_pwds_do_not_match(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_role_and_permission,
    ) -> None:
        data = {
            "email": "elena@gmail.com",
            "password": "mypasswordL@1",
            "confirm_password": "password",
        }
        response = await client.post(
            app.url_path_for("auth:register-new-user"),
            json=data,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_register_user_account_email_exists(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_user: UserAuthSchema,
    ) -> None:
        user_schema = UserCreate(
            email="fakeuser@gmail.com",
            password="mypasswordL1@",
            confirm_password="mypasswordL1@",
        )
        response = await client.post(
            app.url_path_for("auth:register-new-user"),
            json=user_schema.model_dump(),
        )
        assert response.status_code == status.HTTP_409_CONFLICT


class TestUserAuthLogin:

    async def test_auth_user_issue_jwt_valid_input(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_user: UserAuthSchema,
    ) -> None:
        data = {
            "username": "fakeuser@gmail.com",
            "password": "secretpasswordD1@",
        }
        response = await client.post(
            app.url_path_for("auth:auth-user-issue-jwt"),
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        access_token = response.json().get("access_token")
        refresh_token = response.json().get("refresh_token")
        token_type = response.json().get("token_type")
        assert access_token != ""
        assert refresh_token != ""
        assert token_type == "Bearer"
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize(
        "payload, status_code",
        [
            (
                {
                    "username": "example@gmail.com",
                    "password": "secretpasswordD1@",
                },
                401,
            ),
            (
                {
                    "username": "fakeuser@gmail.com",
                    "password": "mypasswordD1@",
                },
                401,
            ),
        ],
    )
    async def test_auth_user_issue_jwt_wrong_email_or_pwd(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_user: UserAuthSchema,
        payload: dict[str, str],
        status_code: int,
    ) -> None:
        response = await client.post(
            app.url_path_for("auth:auth-user-issue-jwt"),
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response_msg = response.json().get("detail")
        assert response_msg == "Invalid email or password"
        assert response.status_code == status_code

    async def test_auth_user_issue_jwt_inactive_user(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_fake_inactive_user: UserAuthSchema,
    ) -> None:
        data = {
            "username": "fakeuser@gmail.com",
            "password": "secretpasswordD1@",
        }
        response = await client.post(
            app.url_path_for("auth:auth-user-issue-jwt"),
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response_msg = response.json().get("detail")
        assert response_msg == "User inactive"
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUserAuthRefreshToken:

    async def test_auth_user_refresh_jwt(
        self,
        app: FastAPI,
        authorized_client_refresh_jwt: AsyncClient,
    ) -> None:
        response = await authorized_client_refresh_jwt.post(app.url_path_for("auth:auth-user-refresh-jwt"))
        access_token = response.json().get("access_token")
        token_type = response.json().get("token_type")
        assert access_token != ""
        assert token_type == "Bearer"
        assert response.status_code == status.HTTP_200_OK

    async def test_auth_user_refresh_jwt_invalid_token_type(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
    ) -> None:
        response = await authorized_client.post(app.url_path_for("auth:auth-user-refresh-jwt"))
        response_msg = response.json().get("detail")
        assert response_msg == "Invalid token type 'access' expected 'refresh'"
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_auth_user_refresh_jwt_unauthorized_user(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        response = await client.post(app.url_path_for("auth:auth-user-refresh-jwt"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "headers",
        [
            ({"Authorization": "Bearer "}),
            ({"Authorization": f"Bearer {token_hex()}"}),
        ],
    )
    async def test_auth_user_refresh_jwt_empty_token_or_wrong_token(
        self,
        app: FastAPI,
        client: AsyncClient,
        headers: dict[str, str],
    ) -> None:
        response = await client.post(
            app.url_path_for("auth:auth-user-refresh-jwt"),
            headers=headers,
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserAuthSelfInfo:
    async def test_user_auth_check_self_info_without_profile(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        create_fake_user: UserAuthSchema,
    ) -> None:
        response = await authorized_client.get(app.url_path_for("auth:user-auth-check-self-info"))
        user_info_schema = UserAuthInfo(profile=None, **response.json())
        assert user_info_schema.email == create_fake_user.email
        assert user_info_schema.email_verified == create_fake_user.email_verified
        assert response.status_code == status.HTTP_200_OK

    async def test_user_auth_check_self_info_with_customer_profile(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_fake_customer_profile: UserAuthSchema,
    ) -> None:
        response = await authorized_client_customer.get(app.url_path_for("auth:user-auth-check-self-info"))
        profile_response = UserAuthProfile(**response.json().get("profile"))
        assert profile_response.user_id == create_fake_customer_profile.id
        assert profile_response.register_as == "customer"
        assert response.status_code == status.HTTP_200_OK

    async def test_user_auth_check_self_info_with_cleaner_profile(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        create_fake_cleaner_profile: UserAuthSchema,
    ) -> None:
        response = await authorized_client_cleaner.get(app.url_path_for("auth:user-auth-check-self-info"))
        profile_response = UserAuthProfile(**response.json().get("profile"))
        assert profile_response.user_id == create_fake_cleaner_profile.id
        assert profile_response.register_as == "cleaner"
        assert response.status_code == status.HTTP_200_OK

    async def test_user_auth_check_self_info_unauthorized_user(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        response = await client.get(
            app.url_path_for("auth:user-auth-check-self-info"),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestVerifyEmail:

    async def test_verify_email(
        self,
        mock_send_email: AsyncMock,
        authorized_client: AsyncClient,
    ) -> None:
        message = mock_send_email.message
        link = re.search('(?<=href=")(.*?)(?=")', message)
        response = await authorized_client.get(link.group())
        resp_js = response.json()
        assert resp_js["email"] == "fakeuser@gmail.com"
        assert resp_js["email_verified"] is True

    async def test_verify_email_user_not_found(
        self,
        mock_send_email: AsyncMock,
        authorized_client: AsyncClient,
        get_email_token: str,
    ) -> None:
        message = mock_send_email.message
        new_link = replace_link_token(msg=message, token=get_email_token)
        response = await authorized_client.get(new_link)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_verify_email_invalid_token(
        self,
        mock_send_email: AsyncMock,
        authorized_client: AsyncClient,
    ) -> None:
        message = mock_send_email.message
        new_link = replace_link_token(msg=message, token=token_urlsafe())
        response = await authorized_client.get(new_link)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
