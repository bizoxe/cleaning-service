from logging import Formatter
from typing import override

from gunicorn.glogging import Logger

from core.config import settings


class GunicornLogger(Logger):
    """
    A subclass of gunicorn.glogging.Logger.
    Overrides the format of access and error logs and logging levels.
    """

    @override
    def setup(self, cfg) -> None:
        super().setup(cfg=cfg)

        self.error_log.setLevel(settings.gunicorn.error_log_lvl)
        self.access_log.setLevel(settings.gunicorn.access_log_lvl)

        self._set_handler(
            log=self.access_log,
            output=cfg.accesslog,
            fmt=Formatter(
                fmt=settings.log_cfg.log_format,
                datefmt=settings.log_cfg.date_fmt,
            ),
        )

        self._set_handler(
            log=self.error_log,
            output=cfg.errorlog,
            fmt=Formatter(
                fmt=settings.log_cfg.log_format,
                datefmt=settings.log_cfg.date_fmt,
            ),
        )
