__all__ = ("main",)

from core.gunicorn import (
    StandaloneApplication,
    get_app_options,
    get_number_of_workers,
)
from main import app
from core.config import settings


def main():
    StandaloneApplication(
        application=app,
        options=get_app_options(
            host=settings.gunicorn.host,
            port=settings.gunicorn.port,
            timeout=settings.gunicorn.timeout,
            workers=get_number_of_workers(),
            log_level=settings.log_cfg.log_level,
        ),
    ).run()


if __name__ == "__main__":
    main()
