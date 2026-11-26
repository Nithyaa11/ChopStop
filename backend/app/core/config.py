"""App settings, loaded from environment variables / the repo-root .env file.

Guardrails: the app refuses to start with weak secrets or a wildcard CORS origin,
and secret values are wrapped in SecretStr so they never show up in logs or reprs.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

# backend/app/core/config.py -> repo root is three levels above "core"
REPO_ROOT = Path(__file__).resolve().parents[3]

PLACEHOLDER_VALUES = {"change-me", "changeme", "secret", "password", ""}
MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # .env also holds POSTGRES_* vars used only by docker compose
    )

    app_env: Literal["development", "test", "production"] = "development"
    # Limited app user (chopstop_app). Used by the running backend.
    database_url: SecretStr
    # Table owner. Used ONLY by Alembic migrations and the role setup script.
    migrator_database_url: SecretStr | None = None
    jwt_secret: SecretStr
    jwt_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_be_strong(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if raw.lower() in PLACEHOLDER_VALUES or len(raw) < MIN_SECRET_LENGTH:
            raise ValueError(
                f"JWT_SECRET must be a random value of at least {MIN_SECRET_LENGTH} characters"
            )
        return value

    @field_validator("database_url", "migrator_database_url")
    @classmethod
    def database_url_must_not_use_placeholder(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and ":change-me@" in value.get_secret_value():
            raise ValueError("Database URL still contains the placeholder password")
        return value

    @model_validator(mode="after")
    def app_and_migrator_must_be_different_users(self) -> "Settings":
        if self.migrator_database_url is None:
            return self
        app_user = make_url(self.database_url.get_secret_value()).username
        owner = make_url(self.migrator_database_url.get_secret_value()).username
        if app_user == owner:
            raise ValueError(
                "DATABASE_URL and MIGRATOR_DATABASE_URL must use different database users"
            )
        return self

    @field_validator("jwt_expire_minutes")
    @classmethod
    def token_lifetime_must_be_short(cls, value: int) -> int:
        if not 5 <= value <= 24 * 60:
            raise ValueError("JWT_EXPIRE_MINUTES must be between 5 and 1440")
        return value

    @field_validator("cors_origins")
    @classmethod
    def cors_must_be_explicit(cls, value: str) -> str:
        origins = [o.strip() for o in value.split(",") if o.strip()]
        if not origins or any("*" in o for o in origins):
            raise ValueError("CORS_ORIGINS must list explicit origins; wildcards are not allowed")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from env
