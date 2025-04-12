import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import ORJSONResponse
from starlette.responses import HTMLResponse

from core.config import settings
from core.models import db_helper
from server.utils.middlewares import PaginationMiddleware
from utils.custom_logger.middlewares import LoggingMiddleware
from utils.custom_logger.setup import setup_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    queue_handler = logging.getHandlerByName("queue_handler")
    queue_handler.listener.start()

    yield
    await db_helper.dispose()
    queue_handler.listener.stop()


def _init_router(_app: FastAPI) -> None:
    from api import router

    _app.include_router(router)


def _init_middleware(_app: FastAPI) -> None:
    _app.add_middleware(PaginationMiddleware)
    _app.middleware("http")(LoggingMiddleware())


def _register_static_docs_routes(_app: FastAPI) -> None:
    @_app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url=str(_app.openapi_url),
            title=_app.title + " - Swagger UI",
            oauth2_redirect_url=_app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
        )

    @_app.get(str(_app.swagger_ui_oauth2_redirect_url), include_in_schema=False)
    async def swagger_ui_redirect() -> HTMLResponse:
        return get_swagger_ui_oauth2_redirect_html()

    @_app.get("/redoc", include_in_schema=False)
    async def redoc_html() -> HTMLResponse:
        return get_redoc_html(
            openapi_url=str(_app.openapi_url),
            title=_app.title + " - ReDoc",
            redoc_js_url="https://unpkg.com/redoc@next/bundles/redoc.standalone.js",
        )


def create_app(
    create_custom_static_urls: bool = False,
) -> FastAPI:
    _app = FastAPI(
        default_response_class=ORJSONResponse,
        title=settings.api.name,
        version=settings.api.version,
        lifespan=lifespan,
        docs_url=None if create_custom_static_urls else "/docs",
        redoc_url=None if create_custom_static_urls else "/redoc",
    )
    _init_router(_app)
    _init_middleware(_app)
    if create_custom_static_urls:
        _register_static_docs_routes(_app=_app)

    return _app
