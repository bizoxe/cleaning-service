import logging
from uuid import UUID

from sqlalchemy import (
    Integer,
    and_,
    cast,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.evaluations.models import CleanerEvaluation
from api.api_v1.evaluations.schemas import (
    CleanerInfo,
    EvaluationAggregate,
    EvaluationInDB,
    EvaluationPublic,
)
from api.api_v1.users.models import User
from crud.base import CRUDRepository

logger = logging.getLogger(__name__)


class EvaluationsCRUD(CRUDRepository):  # type: ignore

    async def get_evaluation(
        self,
        session: AsyncSession,
        owner: UUID,
        cleaner_id: UUID,
    ) -> CleanerEvaluation | None:
        """
        Gets the cleaning specialist's evaluation by owner
        ID and cleaner ID.
        Args:
            session: The database session.
            owner: The ID of the user who evaluated the cleaner's job.
            cleaner_id: Cleaning specialist identifier.

        Returns:
                CleanerEvaluation object if found, otherwise None.
        """
        logger.debug("getting %s by owner=%s and cleaner_id=%s", self._name, owner, cleaner_id)
        res = await session.scalar(
            select(CleanerEvaluation).where(
                and_(
                    CleanerEvaluation.owner == owner,
                    CleanerEvaluation.cleaner_id == cleaner_id,
                )
            )
        )

        return res

    async def create_evaluation(
        self,
        session: AsyncSession,
        evaluation: EvaluationInDB,
    ) -> EvaluationPublic | None:
        """
        Creates an evaluation for the cleaning specialist.
        Args:
            session: The database session.
            evaluation: Input data for creating the evaluation.

        Returns:
            EvaluationPublic (pydantic model object) | None: EvaluationPublic
            object if the evaluation does not exist in the database, otherwise None.
        """
        if await self.get_evaluation(
            session=session,
            owner=evaluation.owner,
            cleaner_id=evaluation.cleaner_id,
        ):
            return None

        to_create = await self.create_record(
            session=session,
            obj_in=evaluation,
        )

        return EvaluationPublic(**to_create.as_dict())

    @staticmethod
    async def get_cleaner_info(
        session: AsyncSession,
        user_id: UUID,
    ) -> CleanerInfo | None:
        """
        Gets information about the cleaning specialist
        from the user's profile field.
        Args:
            session: The database session.
            user_id: User identifier.

        Returns:
            CleanerInfo (pydantic model object) | None: CleanerInfo object
            if the user exists in the database, otherwise None.
        """
        if res := await session.get(User, user_id):
            cleaner_info = res.profile[0]
            return CleanerInfo(**cleaner_info.as_dict())

        return None

    async def get_all_cleaner_evaluations(
        self,
        session: AsyncSession,
        cleaner: CleanerInfo,
        offset: int,
        limit: int,
    ) -> list[EvaluationPublic]:
        """
        Gets all evaluations for the cleaning specialist.
        Args:
            session: The database session.
            cleaner: Input data for the identification of the cleaner.
            offset: Number of records to skip.
            limit: Maximum number of records to retrieve.

        Returns:
                list[EvaluationPublic]: List of EvaluationPublic objects.
        """
        result = await self.get_many_records(
            session=session,
            cleaner_id=cleaner.user_id,
            offset=offset,
            limit=limit,
        )

        return [EvaluationPublic(**res.as_dict()) for res in result]

    @staticmethod
    async def get_cleaner_aggregates(
        session: AsyncSession,
        cleaner: CleanerInfo,
    ) -> EvaluationAggregate:
        """
        Gets general statistics about the cleaning specialist.
        Args:
            session: The database session.
            cleaner: Input data for the identification of the cleaner.

        Returns:
            EvaluationAggregate (pydantic model object): EvaluationAggregate object.
        """
        stmt = (
            select(
                CleanerEvaluation.cleaner_id,
                func.avg(CleanerEvaluation.professionalism).label("avg_professionalism"),
                func.avg(CleanerEvaluation.completeness).label("avg_completeness"),
                func.avg(CleanerEvaluation.efficiency).label("avg_efficiency"),
                func.avg(CleanerEvaluation.overall_rating).label("avg_overall_rating"),
                func.min(CleanerEvaluation.overall_rating).label("min_overall_rating"),
                func.max(CleanerEvaluation.overall_rating).label("max_overall_rating"),
                func.count(CleanerEvaluation.owner).label("total_evaluations"),
                func.sum(cast(CleanerEvaluation.no_show, Integer)).label("total_no_show"),
                func.count(CleanerEvaluation.overall_rating)
                .filter(CleanerEvaluation.overall_rating == 1)
                .label("one_stars"),
                func.count(CleanerEvaluation.overall_rating)
                .filter(CleanerEvaluation.overall_rating == 2)
                .label("two_stars"),
                func.count(CleanerEvaluation.overall_rating)
                .filter(CleanerEvaluation.overall_rating == 3)
                .label("three_stars"),
                func.count(CleanerEvaluation.overall_rating)
                .filter(CleanerEvaluation.overall_rating == 4)
                .label("four_stars"),
                func.count(CleanerEvaluation.overall_rating)
                .filter(CleanerEvaluation.overall_rating == 5)
                .label("five_stars"),
            )
            .where(CleanerEvaluation.cleaner_id == cleaner.user_id)
            .group_by(CleanerEvaluation.cleaner_id)
        )

        res = await session.execute(stmt)
        cleaner_aggregates = res.mappings().one()
        evaluation_aggregate = EvaluationAggregate(
            cleaner=cleaner,
            **cleaner_aggregates,
        )

        return evaluation_aggregate


evaluations_crud = EvaluationsCRUD(CleanerEvaluation)
