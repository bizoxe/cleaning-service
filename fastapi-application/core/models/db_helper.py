"""
This module contains a helper class for interacting with the database.
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from core.config import settings


class DataBaseHelper:

    def __init__(
        self,
        url: str,
        echo: bool,
        echo_pool: bool,
        pool_pre_ping: bool,
        pool_size: int,
        max_overflow: int,
    ) -> None:
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_pre_ping=pool_pre_ping,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        """
        Finalising the asynchronous engine.
        """
        await self.engine.dispose()

    async def session_getter(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Use as a dependency for fastapi to get a session.
        """
        async with self.session_factory() as session:
            yield session

    @asynccontextmanager
    async def get_ctx_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager that creates an async session and
        yields it for use in a 'with' statement.
        """
        async with self.session_factory() as session:
            yield session


db_helper = DataBaseHelper(
    url=settings.db.postgres_connection_string,
    echo=settings.db.echo,
    echo_pool=settings.db.echo_pool,
    pool_pre_ping=settings.db.pool_pre_ping,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
)
