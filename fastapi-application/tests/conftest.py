import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import (
    ASGITransport,
    AsyncClient,
)
from pytest_postgresql import factories
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.models import db_helper
from server.create_fastapi_app import create_app
from tests.database import session_manager


class CustomEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    pass


@pytest.fixture(autouse=True)
def app() -> FastAPI:
    _app = create_app()

    return _app


@pytest_asyncio.fixture(scope="function")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Content-Type": "application/json"},
        ) as client:

            yield client


test_db = factories.postgresql_noproc(
    host=settings.db.postgres_host,
    port=settings.db.postgres_port,
    user=settings.db.test_postgres_user,
    password=settings.db.test_postgres_pwd,
    dbname="test_db",
)


@pytest.fixture(scope="session", params=(CustomEventLoopPolicy(),))
def event_loop_policy(request):
    return request.param


@pytest_asyncio.fixture(scope="module", autouse=True)
async def connection_test(
    test_db,
    event_loop_policy,
) -> None:
    pg_host = test_db.host
    pg_port = test_db.port
    pg_user = test_db.user
    pg_password = test_db.password
    pg_db = test_db.dbname
    version = test_db.version
    with DatabaseJanitor(
        user=pg_user,
        host=pg_host,
        port=pg_port,
        dbname=pg_db,
        password=pg_password,
        version=version,
    ):
        connection_str = f"postgresql+psycopg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"

        session_manager.init(connection_str)

        yield
        await session_manager.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def create_tables(connection_test: None) -> None:
    async with session_manager.connect() as connection:
        await session_manager.drop_all(connection)
        await session_manager.create_all(connection)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def session_override(app: FastAPI, connection_test: None) -> None:
    async def get_db_override() -> AsyncGenerator[AsyncSession, None]:
        async with session_manager.session() as session:
            yield session

    app.dependency_overrides[db_helper.session_getter] = get_db_override
