from typing import Any

from core.gunicorn.logger import GunicornLogger


def get_app_options(
    host: str,
    port: int,
    timeout: int,
    workers: int,
    log_level: str,
) -> dict[str, Any]:

    return {
        "accesslog": "-",
        "errorlog": "-",
        "bind": f"{host}:{port}",
        "loglevel": log_level,
        "logger_class": GunicornLogger,
        "timeout": timeout,
        "workers": workers,
        "worker_class": "uvicorn.workers.UvicornWorker",
    }
