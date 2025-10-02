"""Logging configuration."""

import sys

from loguru import logger

from settings import LogLevel, load_settings

settings = load_settings()


def setup(level: LogLevel | None = None) -> None:
    """Sets up global logging."""
    logger.remove()
    level: str = level or settings.log_level
    logger.add(sys.stderr, level=level)
