"""Configuration for the weather data producer service."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseSettings, ConfigDict


def _get_project_root() -> Path:
    """
    Calculate the project root directory.

    Assumes this file is at src/producer/producer_app/config.py.
    Navigates up 3 levels to reach the project root.

    Returns:
        Path to the project root directory
    """
    current_file_dir: Path = Path(__file__).parent.resolve()
    # producer_app -> producer -> src -> root
    return current_file_dir.parent.parent.parent


class Settings(BaseSettings):
    """
    Producer service configuration.

    Loads settings from environment variables or .env file.
    All settings have sensible defaults except for the API key.
    """

    # API Configuration
    API_KEY: str
    """OpenWeather API key (required, no default)"""

    BASE_URL: str = "http://api.weatherapi.com/v1/current.json"
    """Base URL for weather API"""

    LAT: float = -20.329704
    """Default latitude for weather queries (Vitoria, Brazil)"""

    LON: float = -40.292017
    """Default longitude for weather queries (Vitoria, Brazil)"""

    # RabbitMQ Configuration
    QUEUE_NAME: str = "weather"
    """RabbitMQ queue name"""

    RABBIT_HOST: str = "localhost"
    """RabbitMQ host address"""

    model_config = ConfigDict(
        env_file=str(_get_project_root() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings: Settings = Settings()
