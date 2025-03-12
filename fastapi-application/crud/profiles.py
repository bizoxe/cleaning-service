from typing import Any
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.profiles.models import Profile
from api.api_v1.profiles.schemas import (
    ProfileInDB,
    ProfilePublic,
    ProfileUpdate,
)
from api.api_v1.users.models import User
from crud.base import CRUDRepository


class ProfileCRUD(CRUDRepository):  # type: ignore

    async def get_profile_by_user_id(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> Profile | None:
        """
        Gets the profile by user ID from the database.
        Args:
            session: The database session.
            user_id: User identifier.

        Returns:
                Profile object if found, otherwise None.
        """
        res = await self.get_one_record(
            session=session,
            user_id=user_id,
        )

        return res

    @staticmethod
    async def update_user_role_id(
        session: AsyncSession,
        user_id: UUID,
        values: dict[str, Any],
    ) -> None:
        """
        Updates the user role identifier.
        Args:
            session: The database session.
            user_id: User identifier.
            values: Values for updating user model fields.
        """
        await session.execute(update(User).where(User.id == user_id).values(values))
        await session.commit()

    async def create_profile(
        self,
        session: AsyncSession,
        profile_schema: ProfileInDB,
    ) -> ProfilePublic | None:
        """
        Creates a user profile in the database.

        When creating a profile, the user registers as a customer or a cleaner.
        Change the user role from authorised to customer or cleaner.
        Args:
            session: The database session.
            profile_schema: Input data for creating a user profile.

        Returns:
            ProfilePublic (pydantic model object) | None: Profile object if it
            does not exist in the database, otherwise None.
        """

        if (
            registered_profile := await self.get_profile_by_user_id(  # noqa: F841
                session=session,
                user_id=profile_schema.user_id,
            )
            is None
        ):
            dict_values: dict[str, Any] = {"profile_exists": True}
            if profile_schema.register_as == "customer":
                dict_values.update(role_id=4)
            else:
                dict_values.update(role_id=5)
            profile = await self.create_record(
                session=session,
                obj_in=profile_schema,
            )
            await self.update_user_role_id(
                session=session,
                user_id=profile_schema.user_id,
                values=dict_values,
            )

            return ProfilePublic(**profile.as_dict())

        return None

    async def update_user_self_profile(
        self,
        session: AsyncSession,
        user_id: UUID,
        schema: ProfileUpdate,
    ) -> ProfilePublic:
        """
        Updates the user's profile.

        When creating a user profile, the profile_exists field in the user model is
        replaced with True. Before calling this method, the profile_exists field is
        checked for truth. Therefore, there is definitely a profile in the database.
        Args:
            session: The database session.
            user_id: User identifier.
            schema: Input data for updating a user profile.

        Returns:
            ProfilePublic (pydantic model object): Updated user profile.
        """
        profile = await self.get_profile_by_user_id(
            session=session,
            user_id=user_id,
        )
        to_update = await self.update_record(
            session=session,
            db_obj=profile,
            obj_in=schema,
        )

        return ProfilePublic(**to_update.as_dict())


profiles_crud = ProfileCRUD(Profile)
