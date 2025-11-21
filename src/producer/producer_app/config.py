"""Configuration for the weather data producer service."""

from pydantic_settings import BaseSettings

from pathlib import Path


def _get_project_root() -> Path:
    """
    Calculate the project root directory.

    Assumes this file is at src/producer/producer_app/config.py.
    Navigates up 3 levels to reach the project root.

    """
    current_file_dir = Path(__file__).parent.resolve()
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

    BASE_URL: str = "http://api.weatherapi.com/v1/current.json"

    LAT: float = -20.329704

    LON: float = -40.292017

    # RabbitMQ Configuration
    QUEUE_NAME: str = "weather"

    RABBIT_HOST: str = "localhost"  # change in docker env

    class Config:
        env_file = str(_get_project_root() / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings: Settings = Settings()
