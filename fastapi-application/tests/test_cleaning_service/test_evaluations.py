from collections.abc import (
    Awaitable,
    Callable,
)
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import (
    FastAPI,
    status,
)
from httpx import AsyncClient
from sqlalchemy import insert

from api.api_v1.cleanings.models import Cleaning
from api.api_v1.cleanings.schemas import CleaningPublic
from api.api_v1.evaluations.models import CleanerEvaluation
from api.api_v1.evaluations.schemas import (
    EvaluationAggregate,
    EvaluationCreate,
    EvaluationInDB,
    EvaluationPublic,
)
from api.api_v1.offers.schemas import (
    OfferCompleted,
    OfferPublic,
)
from auth.schemas import UserAuthSchema
from tests.database import session_manager

pytestmark = pytest.mark.asyncio


@pytest.fixture
def create_evaluation() -> EvaluationCreate:
    schema = EvaluationCreate(
        no_show=False,
        headline="cleaning job evaluation",
        comment="some comment",
        professionalism=5,
        completeness=5,
        efficiency=5,
        overall_rating=5,
    )

    return schema


@pytest_asyncio.fixture(scope="function")
async def get_completed_offer(
    change_offer_status: Callable[[str], Awaitable[OfferPublic]],
) -> OfferCompleted:
    set_status = await change_offer_status("completed")
    async with session_manager.session() as session:
        cleaning = await session.get(Cleaning, set_status.cleaning_id)

        return OfferCompleted(
            cleaner_id=cleaning.owner,
            status=set_status.status,
        )


@pytest_asyncio.fixture(scope="function")
async def create_eval_in_db(
    get_completed_offer: OfferCompleted,
    create_fake_customer_profile: UserAuthSchema,
    create_evaluation: EvaluationCreate,
) -> EvaluationPublic:
    eval_in_db = EvaluationInDB(
        owner=create_fake_customer_profile.id,
        cleaner_id=get_completed_offer.cleaner_id,
        **create_evaluation.model_dump(),
    )
    async with session_manager.session() as session:
        evaluation = CleanerEvaluation(**eval_in_db.model_dump())
        session.add(evaluation)
        await session.commit()
        await session.refresh(evaluation)

        return EvaluationPublic(**evaluation.as_dict())


@pytest_asyncio.fixture(scope="function")
async def create_evals_for_pagination(
    create_fake_cleaning: CleaningPublic,
    create_evaluation: EvaluationCreate,
) -> list[CleanerEvaluation]:
    evals_list = []
    for _ in range(1, 151):
        eval_in_db = EvaluationInDB(
            owner=uuid4(),
            cleaner_id=create_fake_cleaning.owner,
            **create_evaluation.model_dump(),
        )
        evals_list.append(eval_in_db)
    async with session_manager.session() as session:
        instances = [{**obj.model_dump()} for obj in evals_list]
        result = await session.scalars(insert(CleanerEvaluation).returning(CleanerEvaluation).values(instances))
        await session.flush()
        await session.commit()

        return result.all()


class TestEvalsUnauthorizedUser:

    async def test_create_evaluation_for_cleaner(
        self,
        app: FastAPI,
        client: AsyncClient,
        get_completed_offer: OfferCompleted,
        create_evaluation: EvaluationCreate,
    ) -> None:
        response = await client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-cleaner",
                cleaner_id=get_completed_offer.cleaner_id,
            ),
            json=create_evaluation.model_dump(),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_show_all_cleaners_evaluations(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        response = await client.get(
            app.url_path_for("evaluations:show-all-cleaners-evaluations"),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_show_all_evaluations_for_cleaner(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_eval_in_db: EvaluationPublic,
    ) -> None:
        response = await client.get(
            app.url_path_for(
                "evaluations:show-all-evaluations-for-cleaner",
                cleaner_id=create_eval_in_db.cleaner_id,
            ),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_show_stats_about_cleaner(
        self,
        app: FastAPI,
        client: AsyncClient,
        create_eval_in_db: EvaluationPublic,
    ) -> None:
        response = await client.get(
            app.url_path_for(
                "evaluations:show-stats-about-cleaner",
                cleaner_id=create_eval_in_db.cleaner_id,
            ),
            headers={**client.headers, "Authorization": "Bearer"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateEvaluations:

    async def test_create_evaluation_for_cleaner(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        get_completed_offer: OfferCompleted,
        create_evaluation: EvaluationCreate,
    ) -> None:
        response = await authorized_client_customer.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-cleaner",
                cleaner_id=get_completed_offer.cleaner_id,
            ),
            json=create_evaluation.model_dump(),
        )
        resp_eval_public = EvaluationPublic(**response.json())
        resp_eval_create = EvaluationCreate(**resp_eval_public.model_dump())
        assert resp_eval_create == create_evaluation
        assert response.status_code == status.HTTP_201_CREATED

    async def test_create_evaluation_already_evaluated(
        self,
        app: FastAPI,
        authorized_client_customer: AsyncClient,
        create_eval_in_db: EvaluationPublic,
        get_completed_offer: OfferCompleted,
        create_evaluation: EvaluationCreate,
    ) -> None:
        response = await authorized_client_customer.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-cleaner",
                cleaner_id=get_completed_offer.cleaner_id,
            ),
            json=create_evaluation.model_dump(),
        )
        msg = response.json().get("detail")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert msg == "You've already evaluated this cleaning specialist"

    async def test_create_eval_cleaner_can_not_evaluate(
        self,
        app: FastAPI,
        authorized_client_cleaner: AsyncClient,
        get_completed_offer: OfferCompleted,
        create_evaluation: EvaluationCreate,
    ) -> None:
        response = await authorized_client_cleaner.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-cleaner",
                cleaner_id=get_completed_offer.cleaner_id,
            ),
            json=create_evaluation.model_dump(),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestShowAllCleaningSpecialistsEvals:

    @pytest.mark.parametrize(
        "max_results, status_code",
        [
            (
                80,
                200,
            ),
            (
                100,
                200,
            ),
        ],
    )
    async def test_show_all_cleaners_evaluations(
        self,
        authorized_client: AsyncClient,
        create_evals_for_pagination: list[CleanerEvaluation],
        max_results: int,
        status_code: int,
    ) -> None:
        response = await authorized_client.get(f"/api/v1/evaluations/all?{max_results=}&descending=false")
        assert response.json().get("count") == max_results
        assert response.status_code == status_code

    async def test_show_all_cleaners_evaluations_check_cursor(
        self,
        authorized_client: AsyncClient,
        create_evals_for_pagination: list[CleanerEvaluation],
    ) -> None:
        response = await authorized_client.get("/api/v1/evaluations/all?max_results=80&descending=false")
        cursor = response.json().get("next_cursor")
        resp_next_items = await authorized_client.get(
            f"/api/v1/evaluations/all?max_results=100&{cursor=}&descending=false"
        )
        residue_elements_in_sequence = len(create_evals_for_pagination) - 80
        assert resp_next_items.json().get("count") == residue_elements_in_sequence
        assert response.status_code == status.HTTP_200_OK


class TestShowAllEvalsForSpecificCleaner:

    async def test_show_all_evaluations_for_cleaner(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        create_eval_in_db: EvaluationPublic,
        create_fake_cleaner_profile: UserAuthSchema,
    ) -> None:
        response = await authorized_client.get(
            app.url_path_for(
                "evaluations:show-all-evaluations-for-cleaner",
                cleaner_id=create_eval_in_db.cleaner_id,
            )
        )
        list_evals_public = [EvaluationPublic(**ev) for ev in response.json()]
        eval_public = list_evals_public[0]
        assert len(list_evals_public) == 1
        assert eval_public.cleaner_id == create_fake_cleaner_profile.id
        assert response.status_code == status.HTTP_200_OK

    async def test_show_all_evaluations_cleaner_not_found(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
    ) -> None:
        response = await authorized_client.get(
            app.url_path_for(
                "evaluations:show-all-evaluations-for-cleaner",
                cleaner_id=uuid4(),
            )
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestShowStatsAboutCleaningSpecialist:

    async def test_show_stats_about_cleaner(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        create_eval_in_db: EvaluationPublic,
        create_fake_cleaner_profile: UserAuthSchema,
    ) -> None:
        response = await authorized_client.get(
            app.url_path_for(
                "evaluations:show-stats-about-cleaner",
                cleaner_id=create_eval_in_db.cleaner_id,
            )
        )
        resp_eval_aggregate = EvaluationAggregate(**response.json())
        assert resp_eval_aggregate.cleaner.user_id == create_fake_cleaner_profile.id
        assert response.status_code == status.HTTP_200_OK

    async def test_show_stats_cleaner_not_found(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
    ) -> None:
        response = await authorized_client.get(
            app.url_path_for(
                "evaluations:show-stats-about-cleaner",
                cleaner_id=uuid4(),
            )
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
