from uuid import UUID
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDRepository
from api.api_v1.cleanings.schemas import (
    CleaningInDB,
    CleaningPublic,
    CleaningUpdate,
)
from api.api_v1.cleanings.models import Cleaning


class CleaningCRUD(CRUDRepository):  # type: ignore
    async def create_cleaning(
        self,
        session: AsyncSession,
        cleaning: CleaningInDB,
    ) -> CleaningPublic:
        """
        Creates a new cleaning in the database.
        Args:
            session: The database session.
            cleaning: Input data for the creation of a cleaning object.

        Returns:
            CleaningPublic (pydantic model object): Newly created cleaning object.
        """
        created_cleaning: Cleaning = await self.create_record(
            session=session,
            obj_in=cleaning,
        )

        return CleaningPublic(**created_cleaning.as_dict())

    async def get_one_cleaning_by_id(
        self,
        session: AsyncSession,
        cleaning_id: int,
    ) -> Cleaning | None:
        """
        Gets cleaning by ID.
        Args:
            session: The database session.
            cleaning_id: Cleaning identifier.

        Returns:
                Cleaning object if found, otherwise None.
        """
        cleaning: Cleaning | None = await self.get_one_by_id(
            session=session,
            obj_id=cleaning_id,
        )

        return cleaning

    async def update_cleaning(
        self,
        session: AsyncSession,
        db_obj: Cleaning,
        to_update: CleaningUpdate,
    ) -> CleaningPublic:
        """
        Updates cleaning in the database.
        Args:
            session: The database session.
            db_obj: Cleaning object retrieved from the database by identifier.
            to_update: Input data for updating the cleaning object.

        Returns:
            CleaningPublic (pydantic model object): Updated cleaning object.
        """
        updated_cleaning: Cleaning = await self.update_record(
            session=session,
            db_obj=db_obj,
            obj_in=to_update,
        )

        return CleaningPublic(**updated_cleaning.as_dict())

    async def delete_cleaning(
        self,
        session: AsyncSession,
        db_obj: Cleaning,
    ) -> None:
        """
        Deletes cleaning from the database.
        Args:
            session: The database session.
            db_obj: Cleaning object retrieved from the database by identifier.
        """
        await self.delete_record(
            session=session,
            db_obj=db_obj,
        )

    async def get_all_cleanings(
        self, session: AsyncSession, user_id: UUID
    ) -> Sequence[Cleaning]:
        """
        Retrieves all cleaning objects from the database by owner field.
        Args:
            session: The database session.
            user_id: User identifier.

        Returns:
                Sequence of cleaning objects.
        """
        cleanings: Sequence[Cleaning] = await self.get_many_records(
            session=session, owner=user_id
        )

        return cleanings


cleanings_crud = CleaningCRUD(Cleaning)
