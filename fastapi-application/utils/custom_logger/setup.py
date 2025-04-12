"""
This module contains the logging configuration.
"""

import logging.config
from pathlib import Path

import yaml

from core.config import settings


def setup_logging(
    log_dir: Path = settings.log_cfg.log_dir,
    log_level: str = settings.log_cfg.log_level,
    to_file: bool = settings.log_cfg.to_file,
    cfg_yaml_file: Path = settings.log_cfg.default_log_cfg_yaml,
    env: str = settings.api.environment,
) -> None:
    level = "DEBUG" if env == "dev" else log_level

    with open(cfg_yaml_file, "rt") as in_file:
        config = yaml.safe_load(in_file)

    config["loggers"]["main"]["level"] = level

    if to_file:
        log_dir.mkdir(exist_ok=True)
        config["handlers"]["queue_handler"]["handlers"].extend(["info_file_handler", "error_file_handler"])

    logging.config.dictConfig(config)
