from pydantic_settings import BaseSettings
from pathlib import Path

# Get the directory where this file is located
current_file_dir = Path(__file__).parent.resolve()

# Calculate the project root directory (assuming this file is at src/producer/producer_app/config.py)
# We want to go up 3 levels to reach the root: producer_app -> producer -> src -> root
project_root = current_file_dir.parent.parent.parent


class Settings(BaseSettings):
    API_KEY: str
    QUEUE_NAME: str = "weather"
    BASE_URL: str = "http://api.weatherapi.com/v1/current.json"
    LAT: float = -20.329704
    LON: float = -40.292017
    RABBIT_HOST: str = "localhost"

    class Config:
        env_file = str(project_root / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
