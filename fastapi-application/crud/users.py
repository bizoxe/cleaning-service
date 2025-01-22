from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDRepository
from api.api_v1.users.models import User
from api.api_v1.users.schemas import (
    UserCreate,
    UserInDB,
    UserPublic,
)
from auth.utils.auth_utils import hash_password
from auth.schemas import UserAuthSchema


class UserCRUD(CRUDRepository):  # type: ignore

    async def get_user_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> User | None:
        """
        Retrieves the user from the database by e-mail.
        Args:
            session: The database session.
            email:  The email of the user to retrieve.

        Returns:
                User object if found, otherwise None.
        """
        res = await self.get_one_record(session=session, email=email)

        return res

    async def create_user(
        self,
        session: AsyncSession,
        user_schema: UserCreate,
    ) -> UserPublic | None:
        """
        Creates a new user in the database.
        Args:
            session: The database session.
            user_schema: Input data for creating a new user.

        Returns:
            UserPublic (pydantic model object) | None: User object or None if the mail is not unique.
        """
        unique_email = await self.get_user_by_email(
            session=session,
            email=user_schema.email,
        )
        if unique_email is None:
            user_pwd_to_bytes: bytes = hash_password(
                plaintext_password=user_schema.password
            )
            user_from_schema = user_schema.model_dump()
            user_from_schema.update(password=user_pwd_to_bytes)
            user_in_db = UserInDB(**user_from_schema)
            user: User = await self.create_record(session=session, obj_in=user_in_db)

            return UserPublic(**user.as_dict())

        return None

    async def get_user_by_id(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> UserAuthSchema | None:
        """
        Gets the user by ID.
        Args:
            session: The database session.
            user_id(UUID): User identifier.

        Returns:
            UserAuthSchema (pydantic model object) | None: User object if found, otherwise None.
        """
        user: User | None = await self.get_one_by_id(session=session, obj_id=user_id)
        if user is not None:
            return UserAuthSchema(
                id=user.id,
                email=user.email,
                email_verified=user.email_verified,
                is_active=user.is_active,
                permissions=[perm.name for perm in user.role.permissions],
            )

        return None


users_crud = UserCRUD(User)
