from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from core.config import settings
from core.models import db_helper


@asynccontextmanager
async def lifespan(_app: FastAPI):

    yield
    await db_helper.dispose()


def _init_middleware(_app: FastAPI) -> None:
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=settings.api.cors_allow_credentials,
        allow_methods=settings.api.cors_allow_methods,
        allow_headers=settings.api.cors_allow_headers,
    )


def create_app() -> FastAPI:
    _app = FastAPI(
        default_response_class=ORJSONResponse,
        title=settings.api.name,
        version=settings.api.version,
        lifespan=lifespan,
    )
    _init_middleware(_app)

    return _app


app = create_app()
