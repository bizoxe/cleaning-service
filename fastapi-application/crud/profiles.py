from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDRepository
from api.api_v1.profiles.models import Profile
from api.api_v1.profiles.schemas import (
    ProfileInDB,
    ProfilePublic,
    ProfileUpdate,
)


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
        res = await self.get_one_record(session=session, user_id=user_id)

        return res

    async def create_profile(
        self,
        session: AsyncSession,
        profile_schema: ProfileInDB,
    ) -> ProfilePublic | None:
        """
        Creates a user profile in the database.
        Args:
            session: The database session.
            profile_schema: Input data for creating a user profile.

        Returns:
            ProfilePublic (pydantic model object) | None: Profile object if it
            does not exist in the database, otherwise None.
        """

        if (
            registered_profile := await self.get_profile_by_user_id(
                session=session, user_id=profile_schema.user_id
            )
            is None
        ):
            profile = await self.create_record(
                session=session,
                obj_in=profile_schema,
            )
            return ProfilePublic(**profile.as_dict())

        return None

    async def update_user_self_profile(
        self,
        session: AsyncSession,
        user_id: UUID,
        schema: ProfileUpdate,
    ) -> ProfilePublic | None:
        """
        Updates the user's profile.
        Args:
            session: The database session.
            user_id: User identifier.
            schema: Input data for updating a user profile.

        Returns:
            ProfilePublic (pydantic model object) | None: Updated user profile if it exists
            in the database, otherwise None.
        """
        if profile := await self.get_profile_by_user_id(
            session=session, user_id=user_id
        ):
            to_update = await self.update_record(
                session=session,
                db_obj=profile,
                obj_in=schema,
            )

            return ProfilePublic(**to_update.as_dict())

        return None


profiles_crud = ProfileCRUD(Profile)
