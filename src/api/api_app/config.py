"""Configuration for the weather data API service."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


def _get_project_root() -> Path:
    """
    Calculate the project root directory.

    Assumes this file is at src/api/api_app/config.py.
    Navigates up 3 levels to reach the project root.

    Returns:
        Path to the project root directory
    """
    current_file_dir: Path = Path(__file__).parent.resolve()
    # api_app -> api -> src -> root
    return current_file_dir.parent.parent.parent


class Settings(BaseSettings):
    """
    API service configuration.

    Loads settings from environment variables or .env file.
    Database and API settings have sensible defaults for local development.
    """

    # Database Configuration
    POSTGRES_USER: str = "weather_user"
    """PostgreSQL database user"""

    POSTGRES_PASSWORD: str = "weather_password"
    """PostgreSQL database password"""

    POSTGRES_DB: str = "weather_db"
    """PostgreSQL database name"""

    POSTGRES_HOST: str = "localhost"
    """PostgreSQL host address"""

    POSTGRES_PORT: int = 5432
    """PostgreSQL port number"""

    # API Configuration
    API_HOST: str = "0.0.0.0"
    """FastAPI server host (0.0.0.0 for Docker container)"""

    API_PORT: int = 8000
    """FastAPI server port"""

    model_config = ConfigDict(
        env_file=str(_get_project_root() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        """
        Construct PostgreSQL connection URL from components.

        Returns:
            PostgreSQL connection string in format postgresql://user:pass@host:port/db
        """
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings: Settings = Settings()
