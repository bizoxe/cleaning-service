import pytest_asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy import update

from api.api_v1.users.models import (
    Role,
    Permission,
)
from tests.database import session_manager
from auth.schemas import (
    UserAuthSchema,
    TokenInfo,
)
from api.api_v1.users.schemas import (
    UserCreate,
    UserInDB,
)
from auth.utils.auth_utils import hash_password
from api.api_v1.users.models import User
from api.api_v1.users.jwt_helpers import create_access_token
from api.api_v1.profiles.schemas import (
    ProfileCreate,
    ProfileInDB,
    ProfilePublic,
)
from api.api_v1.profiles.models import Profile


@pytest_asyncio.fixture(scope="function")
async def create_fake_role_and_permission(connection_test) -> None:
    user_role = Role(id=1, name="UserAuth")
    read_permission = Permission(name="read")
    modify_permission = Permission(name="modify")
    user_role.permissions.extend([read_permission, modify_permission])
    async with session_manager.session() as session:
        session.add(user_role)
        await session.commit()


@pytest_asyncio.fixture(scope="function")
async def create_fake_user(
    create_fake_role_and_permission, connection_test
) -> UserAuthSchema:
    user_schema = UserCreate(
        email="fakeuser@gmail.com",
        password="secretpasswordD1@",
        confirm_password="secretpasswordD1@",
    )
    str_pwd_to_bytes: bytes = hash_password(plaintext_password=user_schema.password)
    user_from_schema = user_schema.model_dump()
    user_from_schema.update(password=str_pwd_to_bytes)
    user_in_db = UserInDB(**user_from_schema)
    async with session_manager.session() as session:
        user = User(**user_in_db.model_dump())
        session.add(user)
        await session.commit()
        await session.refresh(user)

        return UserAuthSchema(
            id=user.id,
            email=user.email,
            email_verified=user.email_verified,
            is_active=user.is_active,
            permissions=[perm.name for perm in user.role.permissions],
        )


@pytest.fixture(scope="function")
def authorized_client(
    client: AsyncClient,
    create_fake_user: UserAuthSchema,
) -> AsyncClient:
    access_token = create_access_token(user=create_fake_user)
    token_schema = TokenInfo(access_token=access_token)
    client.headers = {
        **client.headers,
        "Authorization": f"{token_schema.token_type} {token_schema.access_token}",
    }

    return client


@pytest_asyncio.fixture(scope="function")
async def create_fake_profile(
    create_fake_user: UserAuthSchema,
) -> ProfilePublic:
    async with session_manager.session() as session:
        profile_schema = ProfileCreate(
            first_name="Dima",
            last_name="Matveev",
            phone_number="+375(29)999-09-09",
            bio="fake bio",
            avatar="https://example.com/",
        )
        user_profile = profile_schema.model_dump()
        user_profile.update(user_id=create_fake_user.id)
        profile_in_db = ProfileInDB(**user_profile)
        created_profile = Profile(**profile_in_db.model_dump())
        session.add(created_profile)
        await session.commit()
        await session.refresh(created_profile)

    return ProfilePublic(**created_profile.as_dict())


@pytest_asyncio.fixture(scope="function")
async def create_fake_inactive_user(
    create_fake_user: UserAuthSchema,
) -> UserAuthSchema:
    async with session_manager.session() as session:
        res = await session.execute(
            update(User)
            .where(User.id == create_fake_user.id)
            .returning(User)
            .values(is_active=False)
        )
        await session.flush()
        await session.commit()
        user = res.scalar()
        create_fake_user.is_active = user.is_active

        return create_fake_user
