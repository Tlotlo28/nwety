"""Application configuration loaded from environment variables."""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All app settings, validated by pydantic."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Nwety"
    debug: bool = False
    secret_key: str = "change-me"

    database_url: str = "sqlite+aiosqlite:///./nwety.db"

    user_one_name: str = "You"
    user_one_language: str = "en"
    user_two_name: str = "Nwety"
    user_two_language: str = "pt"

    # Deployment
    host: str = "127.0.0.1"
    port: int = 8000

    @property
    def is_production(self) -> bool:
        """True when running on Render (or any host that sets PORT)."""
        return bool(os.getenv("PORT"))


@lru_cache
def get_settings() -> Settings:
    return Settings()