"""Application settings module."""

from functools import cache
from typing import Annotated, Literal

from pydantic import Field
from pydantic_settings import BaseSettings

type LogLevel = Literal[
    "TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"
]


class Settings(BaseSettings):
    """Application settings."""

    log_level: Annotated[LogLevel, Field(description="Logging level")] = "DEBUG"


@cache
def load_settings(**kwargs) -> Settings:
    """Loads application settings."""
    return Settings(**kwargs)
