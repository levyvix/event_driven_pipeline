from pathlib import Path

from pydantic_settings import BaseSettings

# Get the directory where this file is located
current_file_dir = Path(__file__).parent.resolve()

# Calculate the project root directory (assuming this file is at src/api/api_app/config.py)
# We want to go up 3 levels to reach the root: api_app -> api -> src -> root
project_root = current_file_dir.parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database settings
    POSTGRES_USER: str = "weather_user"
    POSTGRES_PASSWORD: str = "weather_password"
    POSTGRES_DB: str = "weather_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    @property
    def database_url(self) -> str:
        """Construct database URL from components"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = str(project_root / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
