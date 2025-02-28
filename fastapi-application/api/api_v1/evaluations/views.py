from typing import (
    Annotated,
    Any,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.evaluations.dependencies import (
    get_cleaner_by_id_from_path,
    get_cleaner_info_with_cleanings,
)
from api.api_v1.evaluations.models import CleanerEvaluation
from api.api_v1.evaluations.schemas import (
    CleanerInfo,
    EvaluationAggregate,
    EvaluationCreate,
    EvaluationInDB,
    EvaluationPublic,
    ItemParamsEvaluation,
)
from auth.dependencies import UserProfilePermissionGetter, get_current_active_auth_user
from auth.schemas import UserAuthSchema
from core.models import db_helper
from crud.evaluations import evaluations_crud
from utils.pagination.paginator import paginate
from utils.pagination.schemas import PaginatedResponse

router = APIRouter(
    tags=["Evaluations"],
)


@router.post(
    "/{cleaner_id}",
    response_model=EvaluationPublic,
    status_code=status.HTTP_201_CREATED,
    name="evaluations:create-evaluation-for-cleaner",
    summary="creating an evaluation for the cleaning specialist",
)
async def create_evaluation_for_cleaner(
    user_auth: Annotated[UserAuthSchema, Depends(UserProfilePermissionGetter("customer"))],
    cleaner: Annotated[CleanerInfo, Depends(get_cleaner_by_id_from_path)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    evaluation: EvaluationCreate,
) -> EvaluationPublic:
    evaluation_in_db = EvaluationInDB(
        owner=user_auth.id,
        cleaner_id=cleaner.user_id,
        **evaluation.model_dump(),
    )
    if created_evaluation := await evaluations_crud.create_evaluation(
        session=session,
        evaluation=evaluation_in_db,
    ):
        return created_evaluation

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="You've already evaluated this cleaning specialist",
    )


@router.get(
    "/all",
    response_model=PaginatedResponse[EvaluationPublic],
    name="evaluations:show-all-cleaners-evaluations",
    summary="show all cleaning specialist evaluations",
    dependencies=[Depends(get_current_active_auth_user)],
)
async def show_all_cleaners_evaluations(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    params: ItemParamsEvaluation = Depends(),
    max_results: int = Query(default=100, ge=1, le=100),
    cursor: str = Query(None),
) -> dict[str, Any]:

    return await paginate(
        session=session,
        model=CleanerEvaluation,
        query=select(CleanerEvaluation),
        max_results=max_results,
        cursor=cursor,
        params=params,
    )


@router.get(
    "/{cleaner_id}",
    response_model=list[EvaluationPublic],
    response_model_exclude_none=True,
    name="evaluations:show-all-evaluations-for-cleaner",
    summary="show all evaluations of one cleaning specialist",
    dependencies=[Depends(get_current_active_auth_user)],
)
async def show_all_evaluations_for_cleaner(
    cleaner: Annotated[CleanerInfo, Depends(get_cleaner_by_id_from_path)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=30),
) -> list[EvaluationPublic]:
    evaluations = await evaluations_crud.get_all_cleaner_evaluations(
        session=session,
        cleaner=cleaner,
        offset=skip,
        limit=limit,
    )

    return evaluations


@router.get(
    "/{cleaner_id}/stats",
    response_model=EvaluationAggregate,
    response_model_exclude_none=True,
    name="evaluations:show-stats-about-cleaner",
    summary="show stats about the cleaning specialist",
    dependencies=[Depends(get_current_active_auth_user)],
)
async def show_stats_about_cleaner(
    cleaner: Annotated[CleanerInfo, Depends(get_cleaner_info_with_cleanings)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> EvaluationAggregate:
    """
    Gets general statistics about the cleaning specialist with information
    about him/her and his/her cleaning job.
    """
    evaluation_aggregate = await evaluations_crud.get_cleaner_aggregates(
        session=session,
        cleaner=cleaner,
    )

    return evaluation_aggregate
