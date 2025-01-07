import uvicorn

from api import router as main_api_router
from server.create_fastapi_app import app
from core.config import settings


app.include_router(
    main_api_router,
)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
