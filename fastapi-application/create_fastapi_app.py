from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):

    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.api.name,
        version=settings.api.version,
        lifespan=lifespan,
    )

    return app
