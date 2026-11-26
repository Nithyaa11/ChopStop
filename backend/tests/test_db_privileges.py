"""Guardrail: the app's database user has the least power possible."""

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import DBAPIError

from app.core.db_roles import (
    APP_DB_ROLE,
    PrivilegedConnectionError,
    assert_least_privilege,
    ensure_app_role,
    privilege_problems,
)
from tests.conftest import APP_URL, OWNER_URL


def test_app_user_passes_least_privilege_check(app_engine: Engine) -> None:
    with app_engine.connect() as conn:
        assert privilege_problems(conn) == []
        assert conn.execute(text("SELECT current_user")).scalar_one() == APP_DB_ROLE


def test_owner_fails_least_privilege_check(owner_engine: Engine) -> None:
    """If someone points the app at the owner/superuser, the startup check catches it."""
    with owner_engine.connect() as conn, pytest.raises(PrivilegedConnectionError):
        assert_least_privilege(conn)


@pytest.mark.parametrize(
    ("statement", "reason"),
    [
        ("ALTER TABLE audit_log DISABLE TRIGGER audit_log_no_update_delete", "disable trigger"),
        ("DROP TABLE audit_log", "drop table"),
        ("CREATE TABLE sneaky (id int)", "create table"),
        ("CREATE ROLE sneaky LOGIN", "create user"),
        ("ALTER ROLE chopstop_app SUPERUSER", "promote itself"),
        ("UPDATE alembic_version SET version_num = 'x'", "tamper with migrations"),
    ],
)
def test_app_user_blocked(app_engine: Engine, statement: str, reason: str) -> None:
    with pytest.raises(DBAPIError), app_engine.begin() as conn:
        conn.execute(text(statement))


def test_ensure_app_role_rejects_wrong_user_or_weak_password() -> None:
    with pytest.raises(ValueError, match="must be"):
        ensure_app_role(OWNER_URL, OWNER_URL)  # owner's name is not chopstop_app
    weak_url = make_url(APP_URL).set(password="short")  # noqa: S106 - deliberately weak
    weak = weak_url.render_as_string(hide_password=False)
    with pytest.raises(ValueError, match="16 characters"):
        ensure_app_role(OWNER_URL, weak)


def test_migration_role_name_matches_code() -> None:
    from importlib import import_module

    migration = import_module("migrations.versions.20261126_0002_app_role_grants")
    assert migration.ROLE == APP_DB_ROLE
