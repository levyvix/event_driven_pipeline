from pydantic_settings import BaseSettings
from pathlib import Path

# Get the directory where this file is located
current_file_dir = Path(__file__).parent.resolve()

# Calculate the project root directory (assuming this file is at src/consumer/consumer_app/config.py)
# We want to go up 3 levels to reach the root: consumer_app -> consumer -> src -> root
project_root = current_file_dir.parent.parent.parent


class Settings(BaseSettings):
    QUEUE_NAME: str = "weather"
    RABBIT_HOST: str = "localhost"
    API_URL: str = "http://localhost:8000/api/weather"  # Internal API endpoint

    class Config:
        env_file = str(project_root / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
