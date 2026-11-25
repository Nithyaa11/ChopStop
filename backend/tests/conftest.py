"""Test setup: every test runs against a separate *_test database, never real data.

Guardrail: before anything else, DATABASE_URL is switched to "<db>_test", and the
session aborts if the database name doesn't end in "_test".
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import OperationalError

from app.core.config import Settings, get_settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _test_database_url() -> str:
    url = make_url(Settings().database_url.get_secret_value())  # type: ignore[call-arg]
    if not (url.database or "").endswith("_test"):
        url = url.set(database=f"{url.database}_test")
    return url.render_as_string(hide_password=False)


# Switch the whole app to the test DB *before* any test module imports app.main
os.environ["DATABASE_URL"] = _test_database_url()
get_settings.cache_clear()


def _assert_test_db(url: str) -> None:
    name = make_url(url).database or ""
    if not name.endswith("_test"):
        pytest.exit(f"Refusing to run tests against non-test database {name!r}", returncode=2)


FAST_FAIL = {"connect_timeout": 3}


def _create_test_db_if_missing(url: str) -> None:
    target = make_url(url)
    admin = create_engine(
        target.set(database="postgres"), isolation_level="AUTOCOMMIT", connect_args=FAST_FAIL
    )
    try:
        conn_ctx = admin.connect()
    except OperationalError:
        pytest.exit(
            "Cannot reach Postgres. Is Docker Desktop running? "
            "Start it, then: docker compose up -d db",
            returncode=3,
        )
    with conn_ctx as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": target.database}
        ).scalar()
        if not exists:
            # Name is derived from settings and checked to end in _test above
            conn.execute(text(f'CREATE DATABASE "{target.database}"'))
    admin.dispose()


def alembic_config() -> Config:
    return Config(str(BACKEND_DIR / "alembic.ini"))


@pytest.fixture(scope="session")
def migrated_test_db() -> Iterator[str]:
    """Only tests that need the DB request this; pure tests run without Docker."""
    url = os.environ["DATABASE_URL"]
    _assert_test_db(url)
    _create_test_db_if_missing(url)
    command.upgrade(alembic_config(), "head")
    yield url


@pytest.fixture
def engine(migrated_test_db: str) -> Iterator[Engine]:
    eng = create_engine(migrated_test_db, connect_args=FAST_FAIL)
    yield eng
    eng.dispose()
