"""Test setup: every test runs against a separate *_test database, never real data.

Guardrails:
  * DATABASE_URL and MIGRATOR_DATABASE_URL are switched to "<db>_test" before any
    test imports the app, and the session aborts if a DB name doesn't end in "_test".
  * Two engines: `app_engine` (limited chopstop_app user, what the real app uses)
    and `owner_engine` (table owner, what migrations use).
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
from app.core.db_roles import ensure_app_role

BACKEND_DIR = Path(__file__).resolve().parents[1]
FAST_FAIL = {"connect_timeout": 3}


def _as_test_db(url: str) -> str:
    parsed = make_url(url)
    if not (parsed.database or "").endswith("_test"):
        parsed = parsed.set(database=f"{parsed.database}_test")
    return parsed.render_as_string(hide_password=False)


_base = Settings()  # type: ignore[call-arg]
if _base.migrator_database_url is None:
    raise RuntimeError("Tests need MIGRATOR_DATABASE_URL (owner) as well as DATABASE_URL")

# Switch the whole app to the test DB *before* any test module imports app.main
APP_URL = _as_test_db(_base.database_url.get_secret_value())
OWNER_URL = _as_test_db(_base.migrator_database_url.get_secret_value())
os.environ["DATABASE_URL"] = APP_URL
os.environ["MIGRATOR_DATABASE_URL"] = OWNER_URL
get_settings.cache_clear()


def _assert_test_db(*urls: str) -> None:
    for url in urls:
        name = make_url(url).database or ""
        if not name.endswith("_test"):
            pytest.exit(f"Refusing to run tests against non-test database {name!r}", returncode=2)


def _create_test_db_if_missing(owner_url: str) -> None:
    target = make_url(owner_url)
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
def migrated_test_db() -> Iterator[None]:
    """Only tests that need the DB request this; pure tests run without Docker."""
    _assert_test_db(APP_URL, OWNER_URL)
    _create_test_db_if_missing(OWNER_URL)
    ensure_app_role(OWNER_URL, APP_URL)
    command.upgrade(alembic_config(), "head")
    yield


@pytest.fixture
def app_engine(migrated_test_db: None) -> Iterator[Engine]:
    """Connects as the limited chopstop_app user, exactly like the running app."""
    eng = create_engine(APP_URL, connect_args=FAST_FAIL)
    yield eng
    eng.dispose()


@pytest.fixture
def owner_engine(migrated_test_db: None) -> Iterator[Engine]:
    """Connects as the table owner (migrations only)."""
    eng = create_engine(OWNER_URL, connect_args=FAST_FAIL)
    yield eng
    eng.dispose()
