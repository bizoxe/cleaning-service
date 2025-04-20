from collections.abc import (
    Awaitable,
    Callable,
)

import pytest
import pytest_asyncio
from httpx import AsyncClient
from pydantic import HttpUrl
from sqlalchemy import and_, update

from api.api_v1.cleanings.models import Cleaning
from api.api_v1.cleanings.schemas import (
    CleaningCreate,
    CleaningInDB,
    CleaningPublic,
    CleaningType,
)
from api.api_v1.offers.models import UserOffer
from api.api_v1.offers.schemas import (
    OfferInDB,
    OfferPublic,
)
from api.api_v1.profiles.models import Profile
from api.api_v1.profiles.schemas import (
    MemberType,
    ProfileCreate,
    ProfileInDB,
)
from api.api_v1.users.jwt_helpers import create_access_token
from api.api_v1.users.models import (
    Permission,
    Role,
    User,
)
from api.api_v1.users.schemas import (
    UserCreate,
    UserInDB,
)
from auth.schemas import (
    TokenInfo,
    UserAuthSchema,
)
from auth.utils.auth_utils import hash_password
from tests.database import session_manager


@pytest_asyncio.fixture(scope="function")
async def create_fake_role_and_permission(connection_test: None) -> None:
    user_role = Role(id=1, name="UserAuth")
    user_customer_role = Role(id=4, name="UserAuthCustomer")
    user_cleaner_role = Role(id=5, name="UserAuthCleaner")

    read_permission = Permission(name="read")
    modify_permission = Permission(name="modify")
    customer = Permission(name="customer")
    cleaner = Permission(name="cleaner")

    user_role.permissions.extend([read_permission, modify_permission])
    user_customer_role.permissions.extend([read_permission, modify_permission, customer])
    user_cleaner_role.permissions.extend([read_permission, modify_permission, cleaner])
    async with session_manager.session() as session:
        session.add_all([user_role, customer, cleaner])
        await session.commit()


@pytest_asyncio.fixture(scope="function")
async def create_fake_user(
    create_fake_role_and_permission: None,
    connection_test: None,
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
            profile_exists=user.profile_exists,
            permissions=[perm.name for perm in user.role.permissions],
        )


@pytest.fixture
def create_specific_user(
    create_fake_role_and_permission: None,
    connection_test: None,
) -> Callable[[str], Awaitable[UserAuthSchema]]:
    async def _create_user(member_type: str) -> UserAuthSchema:
        user_schema = UserCreate(
            email=f"{member_type}@gmail.com",
            password=f"{member_type}passwordD1@",
            confirm_password=f"{member_type}passwordD1@",
        )

        bytes_pwd: bytes = hash_password(plaintext_password=user_schema.password)
        user_from_schema = user_schema.model_dump()
        user_from_schema.update(password=bytes_pwd)
        user_in_db = UserInDB(**user_from_schema)

        async with session_manager.session() as session:
            user = User(**user_in_db.model_dump())
            session.add(user)
            await session.commit()
            await session.refresh(user)
            permissions = [perm.name for perm in user.role.permissions]
            return UserAuthSchema(permissions=permissions, **user.as_dict())

    return _create_user


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


@pytest.fixture
def create_fake_profile() -> Callable[[str, UserAuthSchema], ProfileInDB]:
    def _create_profile(member_type: str, user_in: UserAuthSchema) -> ProfileInDB:
        if member_type == "customer":
            profile_schema = ProfileCreate(
                first_name="Elena",
                last_name="Dolgorukaya",
                phone_number="+375(44)909-09-09",
                register_as=MemberType("customer"),
                bio=f"fake {member_type} bio",
                avatar=HttpUrl("https://example.com/"),
            )
        else:
            profile_schema = ProfileCreate(
                first_name="Dmitry",
                last_name="Matveev",
                phone_number="+375(25)808-99-19",
                register_as=MemberType("cleaner"),
                bio=f"fake {member_type} bio",
                avatar=HttpUrl("https://example.com/"),
            )
        user_profile = profile_schema.model_dump()
        user_profile.update(user_id=user_in.id)
        profile_in_db = ProfileInDB(
            email=user_in.email,
            **user_profile,
        )

        return profile_in_db

    return _create_profile


@pytest_asyncio.fixture(scope="function")
async def create_fake_customer_profile(
    create_specific_user: Callable[[str], Awaitable[UserAuthSchema]],
    create_fake_profile: Callable[[str, UserAuthSchema], ProfileInDB],
) -> UserAuthSchema:
    async with session_manager.session() as session:
        user_auth = await create_specific_user("customer")
        to_create = create_fake_profile("customer", user_auth)
        profile = Profile(**to_create.model_dump())
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        user_auth_customer = await session.scalar(
            update(User).filter_by(id=profile.user_id).values(profile_exists=True, role_id=4).returning(User)
        )
        await session.flush()
        await session.commit()

    permissions = [perm.name for perm in user_auth_customer.role.permissions]

    return UserAuthSchema(
        permissions=permissions,
        **user_auth_customer.as_dict(),
    )


@pytest_asyncio.fixture(scope="function")
async def create_fake_cleaner_profile(
    create_specific_user: Callable[[str], Awaitable[UserAuthSchema]],
    create_fake_profile: Callable[[str, UserAuthSchema], ProfileInDB],
) -> UserAuthSchema:
    async with session_manager.session() as session:
        user_auth = await create_specific_user("cleaner")
        to_create = create_fake_profile("cleaner", user_auth)
        profile = Profile(**to_create.model_dump())
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        user_auth_cleaner = await session.scalar(
            update(User).filter_by(id=profile.user_id).values(profile_exists=True, role_id=5).returning(User)
        )
        await session.flush()
        await session.commit()

    permissions = [perm.name for perm in user_auth_cleaner.role.permissions]

    return UserAuthSchema(
        permissions=permissions,
        **user_auth_cleaner.as_dict(),
    )


@pytest_asyncio.fixture(scope="function")
async def create_fake_inactive_user(
    create_fake_user: UserAuthSchema,
) -> UserAuthSchema:
    async with session_manager.session() as session:
        user = await session.scalar(
            update(User).where(User.id == create_fake_user.id).returning(User).values(is_active=False)
        )
        await session.flush()
        await session.commit()

        return UserAuthSchema(
            id=user.id,
            email=user.email,
            email_verified=user.email_verified,
            is_active=user.is_active,
            profile_exists=user.profile_exists,
            permissions=[perm.name for perm in user.role.permissions],
        )


@pytest.fixture(scope="function")
def authorized_client_cleaner(
    client: AsyncClient,
    create_fake_cleaner_profile: UserAuthSchema,
) -> AsyncClient:
    access_token = create_access_token(user=create_fake_cleaner_profile)
    token_schema = TokenInfo(access_token=access_token)
    client.headers = {
        **client.headers,
        "Authorization": f"{token_schema.token_type} {token_schema.access_token}",
    }

    return client


@pytest.fixture(scope="function")
def authorized_client_customer(
    client: AsyncClient,
    create_fake_customer_profile: UserAuthSchema,
) -> AsyncClient:
    access_token = create_access_token(user=create_fake_customer_profile)
    token_schema = TokenInfo(access_token=access_token)
    client.headers = {
        **client.headers,
        "Authorization": f"{token_schema.token_type} {token_schema.access_token}",
    }

    return client


@pytest.fixture
def create_cleaning() -> CleaningCreate:
    return CleaningCreate(
        name="window cleaning",
        price=20.0,
        description="window cleaning for test",
        cleaning_type=CleaningType("spot clean"),
    )


@pytest_asyncio.fixture(scope="function")
async def create_fake_cleaning(
    create_fake_cleaner_profile: UserAuthSchema,
    create_cleaning: CleaningCreate,
) -> CleaningPublic:
    async with session_manager.session() as session:
        cleaning_schema = create_cleaning.model_dump()
        cleaning_in_db = CleaningInDB(owner=create_fake_cleaner_profile.id, **cleaning_schema)
        cleaning = Cleaning(**cleaning_in_db.model_dump())
        session.add(cleaning)
        await session.commit()
        await session.refresh(cleaning)

        return CleaningPublic(**cleaning.as_dict())


@pytest_asyncio.fixture(scope="function")
async def create_offer_in_db(
    create_fake_customer_profile: UserAuthSchema,
    create_fake_cleaning: CleaningPublic,
) -> OfferPublic:
    async with session_manager.session() as session:
        offer_in_db = OfferInDB(
            offerer_id=create_fake_customer_profile.id,
            cleaning_id=create_fake_cleaning.id,
            status="pending",
            requested_date="2025-02-04",
            requested_time="14:00",
        )
        offer = UserOffer(**offer_in_db.model_dump())
        session.add(offer)
        await session.commit()
        await session.refresh(offer)

        return OfferPublic(**offer.as_dict())


@pytest.fixture
def change_offer_status(create_offer_in_db: OfferPublic) -> Callable[[str], Awaitable[OfferPublic]]:
    async def _change_offer_status(status: str) -> OfferPublic:
        async with session_manager.session() as session:
            updated_offer = await session.scalar(
                update(UserOffer)
                .where(
                    and_(
                        UserOffer.offerer_id == create_offer_in_db.offerer_id,
                        UserOffer.cleaning_id == create_offer_in_db.cleaning_id,
                    )
                )
                .values(status=status)
                .returning(UserOffer)
            )
            await session.flush()
            await session.commit()

        return OfferPublic(**updated_offer.as_dict())

    return _change_offer_status
