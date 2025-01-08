import uvicorn

from server.create_fastapi_app import create_app
from core.config import settings

app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
