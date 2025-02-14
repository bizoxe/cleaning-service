from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from core.config import settings
from core.models import db_helper
from server.utils.middlewares import PaginationMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:

    yield
    await db_helper.dispose()


def _init_router(_app: FastAPI) -> None:
    from api import router

    _app.include_router(router)


def _init_middleware(_app: FastAPI) -> None:
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=settings.api.cors_allow_credentials,
        allow_methods=settings.api.cors_allow_methods,
        allow_headers=settings.api.cors_allow_headers,
    )
    _app.add_middleware(PaginationMiddleware)


def create_app() -> FastAPI:
    _app = FastAPI(
        default_response_class=ORJSONResponse,
        title=settings.api.name,
        version=settings.api.version,
        lifespan=lifespan,
    )
    _init_router(_app)
    _init_middleware(_app)

    return _app
