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

    # OAuth2 / OIDC (Phase 2). All optional: when neither oidc_issuer nor
    # oidc_jwks_url is set, OIDC is disabled and only Basic Auth is accepted.
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None
    oidc_required_scope: str | None = None
    oidc_clock_skew_s: int = 30

    @property
    def oidc_enabled(self) -> bool:
        return bool(self.oidc_issuer or self.oidc_jwks_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
