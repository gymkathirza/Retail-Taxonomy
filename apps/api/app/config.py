"""Application settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://taxonomy:taxonomy@127.0.0.1:5432/taxonomy"
    demo_user: str = "admin"
    demo_password: str = "password"


@lru_cache
def get_settings() -> Settings:
    return Settings()
