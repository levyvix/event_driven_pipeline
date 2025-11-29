"""Configuration for the weather data consumer service."""

from pathlib import Path

from pydantic_settings import BaseSettings


def _get_project_root() -> Path:
    """
    Returns the root of the project
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

    RABBIT_HOST: str = "localhost"

    # Internal API Configuration
    API_URL: str = "http://localhost:8000/api/weather"

    class Config:
        env_file: str = str(_get_project_root() / ".env")
        env_file_encoding: str = "utf-8"
        extra: str = "ignore"


settings: Settings = Settings()
