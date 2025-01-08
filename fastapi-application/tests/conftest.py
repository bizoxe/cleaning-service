from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
)
from alembic import (
    command,
    config,
)
import pytest_asyncio
from httpx import (
    ASGITransport,
    AsyncClient,
)
from asgi_lifespan import LifespanManager

from core.config import settings
from server.create_fastapi_app import create_app
from core.models import db_helper


TEST_DB_URL = str(settings.db.test_db_url)


async_engine: AsyncEngine = create_async_engine(
    url=TEST_DB_URL,
    echo=False,
    echo_pool=False,
)


def run_upgrade(connection, cfg):
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")


def run_downgrade(connection, cfg):
    cfg.attributes["connection"] = connection
    command.downgrade(cfg, "base")


@pytest_asyncio.fixture(scope="function", autouse=True)
async def apply_migrations() -> None:
    """
    Runs migrations before testing.
    """
    alembic_cfg = config.Config("alembic.ini")
    async with async_engine.begin() as conn:
        await conn.run_sync(run_downgrade, alembic_cfg)
        await conn.run_sync(run_upgrade, alembic_cfg)


async def override_session_getter() -> AsyncGenerator[AsyncSession, None]:
    """
    Is used to connect to the test database and get the session.
    Returns:
            The database session.
    """
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=async_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session

    await async_engine.dispose()


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def test_app():
    app = create_app()
    app.dependency_overrides[db_helper.session_getter] = override_session_getter

    return app


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def client(test_app) -> AsyncGenerator[AsyncClient, None]:
    async with LifespanManager(test_app):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:

            yield client
