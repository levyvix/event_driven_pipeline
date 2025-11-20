"""Configuration for the weather data consumer service."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


def _get_project_root() -> Path:
    """
    Calculate the project root directory.

    Assumes this file is at src/consumer/consumer_app/config.py.
    Navigates up 3 levels to reach the project root.

    Returns:
        Path to the project root directory
    """
    current_file_dir: Path = Path(__file__).parent.resolve()
    # consumer_app -> consumer -> src -> root
    return current_file_dir.parent.parent.parent


class Settings(BaseSettings):
    """
    Consumer service configuration.

    Loads settings from environment variables or .env file.
    All settings have sensible defaults for local development.
    """

    # RabbitMQ Configuration
    QUEUE_NAME: str = "weather"
    """RabbitMQ queue name to consume from"""

    RABBIT_HOST: str = "localhost"
    """RabbitMQ host address"""

    # Internal API Configuration
    API_URL: str = "http://localhost:8000/api/weather"
    """Internal weather API endpoint for posting processed messages"""

    model_config = ConfigDict(
        env_file=str(_get_project_root() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings: Settings = Settings()
