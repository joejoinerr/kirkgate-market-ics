"""Application settings module."""

from functools import cache
from pathlib import Path
from typing import Annotated, Literal

import pydantic
from pydantic import Field
from pydantic_settings import BaseSettings

type LogLevel = Literal[
    "TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"
]


class Settings(BaseSettings):
    """Application settings."""

    events_page_url: Annotated[
        str, Field(description="URL of the events page to scrape")
    ]
    openrouter_api_key: Annotated[
        pydantic.SecretStr, Field(description="OpenRouter API key")
    ]
    openrouter_model: Annotated[str, Field(description="OpenRouter model to use")] = (
        "deepseek/deepseek-chat-v3.1:free"
    )
    artifacts_dir: Annotated[
        Path, Field(description="Directory to store artifacts")
    ] = Path("artifacts")
    ics_file_name: Annotated[Path, Field(description="ICS file name")] = Path(
        "events.ics"
    )
    html_file_name: Annotated[Path, Field(description="HTML file name")] = Path(
        "events.html"
    )
    scraper_user_agent: Annotated[
        str, Field(description="User-Agent string for web scraping")
    ] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 15.7; rv:143.0) Gecko/20100101 Firefox/143.0"
    log_level: Annotated[LogLevel, Field(description="Logging level")] = "DEBUG"


@cache
def load_settings(**kwargs) -> Settings:
    """Loads application settings."""
    return Settings(**kwargs)
