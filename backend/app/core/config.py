from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
backend_env = BASE_DIR / ".env"
root_env = BASE_DIR.parent / ".env"

env_file = ".env"
if backend_env.exists():
    env_file = str(backend_env)
elif root_env.exists():
    env_file = str(root_env)


class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_PUBLISHABLE_KEY: str

    model_config = SettingsConfigDict(
        env_file=env_file,
        extra="ignore",
    )


settings = Settings()
