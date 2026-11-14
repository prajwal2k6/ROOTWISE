
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Get the ROOTWISE backend directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Locate the backend .env file
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_PUBLISHABLE_KEY: str

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Create application settings
settings = Settings()
