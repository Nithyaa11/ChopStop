"""Guardrail tests: the app must refuse to start with unsafe settings."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

GOOD = {
    "database_url": "postgresql+psycopg://u:a-real-password@localhost:5432/db",
    "jwt_secret": "x" * 48,
    "cors_origins": "http://localhost:5173",
}


def make(**overrides: object) -> Settings:
    # _env_file=None: test only the values passed in, ignore the real .env
    return Settings(_env_file=None, **{**GOOD, **overrides})  # type: ignore[arg-type]


def test_good_settings_load() -> None:
    settings = make()
    assert settings.cors_origin_list == ["http://localhost:5173"]


@pytest.mark.parametrize("secret", ["change-me", "short", "", "password"])
def test_weak_jwt_secret_rejected(secret: str) -> None:
    with pytest.raises(ValidationError):
        make(jwt_secret=secret)


def test_placeholder_db_password_rejected() -> None:
    with pytest.raises(ValidationError):
        make(database_url="postgresql+psycopg://chopstop:change-me@localhost:5432/chopstop")


@pytest.mark.parametrize("origins", ["*", "http://localhost:5173,*", ""])
def test_wildcard_or_empty_cors_rejected(origins: str) -> None:
    with pytest.raises(ValidationError):
        make(cors_origins=origins)


@pytest.mark.parametrize("minutes", [0, 4, 100_000])
def test_token_lifetime_bounds(minutes: int) -> None:
    with pytest.raises(ValidationError):
        make(jwt_expire_minutes=minutes)


def test_secrets_hidden_in_repr() -> None:
    settings = make()
    assert "a-real-password" not in repr(settings)
    assert "x" * 48 not in repr(settings)


def test_app_and_migrator_must_differ() -> None:
    same = "postgresql+psycopg://chopstop:a-real-password@localhost:5432/db"
    with pytest.raises(ValidationError, match="different database users"):
        make(database_url=same, migrator_database_url=same)


def test_placeholder_migrator_password_rejected() -> None:
    with pytest.raises(ValidationError):
        make(migrator_database_url="postgresql+psycopg://chopstop:change-me@localhost:5432/db")


def test_dev_port_defaults_to_8010_and_is_range_checked() -> None:
    assert make().api_port == 8010
    for bad in (80, 70000):
        with pytest.raises(ValidationError):
            make(api_port=bad)
