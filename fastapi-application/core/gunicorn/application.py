from multiprocessing import cpu_count
from typing import Any

from gunicorn.app.base import BaseApplication
from fastapi import FastAPI


def get_number_of_workers() -> int:

    return (cpu_count() * 2) + 1


class StandaloneApplication(BaseApplication):
    """
    Gunicorn BaseApplication subclass.
    Interface for configuring and loading the application.
    """

    def __init__(
        self,
        application: FastAPI,
        options: dict[str, Any] | None = None,
    ) -> None:
        self.application = application
        self.options = options or {}
        super().__init__()

    def load(self):
        return self.application

    @property
    def config_options(self) -> dict[str, Any]:
        return {
            k: v
            for k, v in self.options.items()
            if k in self.cfg.settings and v is not None
        }

    def load_config(self) -> None:
        for key, value in self.config_options.items():
            self.cfg.set(key.lower(), value)
