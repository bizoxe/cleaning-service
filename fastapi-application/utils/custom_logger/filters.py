import logging
from typing import override


class NonErrorFilter(logging.Filter):
    """
    DEBUG and INFO level messages are logged.
    """

    @override
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return record.levelno <= logging.INFO
