"""
This module contains the base interface for CRUD operations.
"""

from typing import (
    TypeVar,
    Generic,
    Sequence,
)
import logging
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.models import Base


ORMModelType = TypeVar("ORMModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

logger = logging.getLogger(__name__)


class CRUDRepository(Generic[ORMModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ORMModelType]) -> None:
        """
        Initializes the class with the given ORM model.
        Args:
            model (type[ORMModelType]): The ORM model to be initialized.
        """
        self._model: type[ORMModelType] = model
        self._name: str = model.__name__

    async def get_one_by_id(
        self,
        session: AsyncSession,
        obj_id: int | UUID,
    ) -> ORMModelType | None:
        """
        Gets a record by its ID
        Args:
            session: The database session.
            obj_id (int | UUID): The ID of the record to retrieve.

        Returns:
                The retrieved record, or None if not found.
        """
        logger.debug("getting %s by id=%s", self._name, obj_id)
        result = await session.execute(
            select(self._model).filter(self._model.id == obj_id)
        )

        return result.scalar_one_or_none()

    async def get_many_by_ids(
        self,
        session: AsyncSession,
        obj_ids: list[int | UUID],
    ) -> Sequence[ORMModelType]:
        """
        Gets multiple records by their IDs.
        Args:
            session: The database session.
            obj_ids (list[int | UUID]): The IDs of the records to retrieve.

        Returns:
                Sequence of the records found.
        """
        logger.debug("getting %s by ids=%s", self._name, obj_ids)
        result = await session.execute(
            select(self._model).where(self._model.id.in_(obj_ids))
        )

        return result.scalars().all()

    async def create_record(
        self, session: AsyncSession, obj_in: CreateSchemaType
    ) -> ORMModelType:
        """
        Creates a new ORMModel instance and adds it to the session.
        Args:
            session: The database session.
            obj_in: The input data for creating the ORMModel instance.

        Returns:
                The newly created ORMModel instance.
        """
        logger.debug("creating %s with obj_in=%s", self._name, obj_in)
        obj_in_data = obj_in.model_dump(exclude_unset=True, exclude_none=True)
        db_obj: ORMModelType = self._model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        return db_obj

    async def update_record(
        self,
        session: AsyncSession,
        db_obj: ORMModelType,
        obj_in: UpdateSchemaType,
    ) -> ORMModelType:
        """
        Updates the given ORMModel object using the provided session and input data.
        Args:
            session: The database session.
            db_obj: The database object to be updated.
            obj_in: The input data for the update.

        Returns:
                The updated object.
        """
        logger.debug(
            "updating %s db_object=%s with obj_in=%s", self._name, db_obj, obj_in
        )
        to_update = obj_in.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in to_update.items():
            setattr(db_obj, field, value)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        return db_obj

    async def delete_record(
        self,
        session: AsyncSession,
        db_obj: ORMModelType,
    ) -> ORMModelType:
        """
        Deletes the given ORMModel object using the provided session.
        Args:
            session: The database session.
            db_obj: Database object to delete.

        Returns:
                The deleted object.
        """
        logger.debug("deleting %s db_object=%s", self._name, db_obj)
        await session.delete(db_obj)
        await session.commit()

        return db_obj

    async def get_one_record(
        self,
        session: AsyncSession,
        *args,
        **kwargs,
    ) -> ORMModelType | None:
        """
        Retrieves one ORMModelType using the provided session and optional
        arguments and keyword arguments.
        Args:
            session: The database session.
            *args: Variable arguments for filtering. For example filter(User.name == 'John')
            **kwargs: Keyword arguments used for filter_by. For example filter_by(name='John')

        Returns:
                The retrieved record, or None if not found.
        """
        logger.debug("getting %s with args=%s, kwargs=%s", self._name, args, kwargs)
        result = await session.execute(
            select(self._model).filter(*args).filter_by(**kwargs)
        )

        return result.scalars().first()

    async def get_many_records(
        self,
        session: AsyncSession,
        *args,
        offset: int = 0,
        limit: int = 100,
        **kwargs,
    ) -> Sequence[ORMModelType]:
        """
        Retrieves multiple ORMModel objects from the database with optional
        filtering and limiting.
        Args:
            session: The database session.
            *args: Positional arguments for filtering the query. For example filter(User.name == 'John')
            offset: The number of results to skip. Defaults to 0.
            limit: The maximum number of results to return. Defaults to 100.
            **kwargs: Keyword arguments for filtering the query. For example filter_by(name='John')

        Returns:
                Sequence[ORMModelType]: A sequence of ORMModel objects retrieved from the database.
        """
        logger.debug("get all %s with args=%s, kwargs=%s", self._name, args, kwargs)
        result = await session.execute(
            select(self._model)
            .filter(*args)
            .filter_by(**kwargs)
            .offset(offset)
            .limit(limit)
        )

        return result.scalars().all()
