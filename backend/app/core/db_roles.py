"""Least-privilege database users.

Two users:
  * migrator (owner) - creates/alters tables. Used only by Alembic.
  * app (chopstop_app) - used by the running backend. Not superuser, owns nothing,
    can only INSERT/SELECT on audit_log. Rights are granted in migrations.

The app refuses to start if it is connected as a privileged user.
"""

import re

import psycopg
from psycopg import sql
from sqlalchemy import Connection, text
from sqlalchemy.engine import make_url

APP_DB_ROLE = "chopstop_app"
_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


class PrivilegedConnectionError(RuntimeError):
    """The app is connected with more database power than it should have."""


def _psycopg_conninfo(sqlalchemy_url: str) -> str:
    return (
        make_url(sqlalchemy_url).set(drivername="postgresql").render_as_string(hide_password=False)
    )


def ensure_app_role(migrator_url: str, app_url: str) -> None:
    """Create or update the app's login role with the password from app_url.

    Idempotent. Run with the migrator (owner) connection. The role is always
    (re)set to the weakest attributes, even if someone changed them by hand.
    """
    app = make_url(app_url)
    name, password = app.username or "", app.password or ""
    if name != APP_DB_ROLE or not _IDENTIFIER.match(name):
        raise ValueError(f"App database user must be {APP_DB_ROLE!r}, got {name!r}")
    if len(password) < 16:
        raise ValueError("App database password must be at least 16 characters")

    attributes = sql.SQL(
        "LOGIN PASSWORD {pw} NOSUPERUSER NOCREATEDB NOCREATEROLE "
        "NOREPLICATION NOBYPASSRLS NOINHERIT CONNECTION LIMIT 20"
    ).format(pw=sql.Literal(password))

    with psycopg.connect(
        _psycopg_conninfo(migrator_url), autocommit=True, connect_timeout=5
    ) as conn:
        exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (name,)).fetchone()
        verb = "ALTER ROLE {} WITH " if exists else "CREATE ROLE {} WITH "
        conn.execute(sql.SQL(verb).format(sql.Identifier(name)) + attributes)


def privilege_problems(conn: Connection) -> list[str]:
    """Return reasons why the current DB user is too powerful (empty list = OK)."""
    row = conn.execute(
        text(
            """
            SELECT r.rolsuper, r.rolcreaterole, r.rolcreatedb, r.rolbypassrls,
                   (SELECT count(*) FROM pg_tables
                     WHERE schemaname = 'public' AND tableowner = current_user) AS owned_tables,
                   (SELECT d.datdba = r.oid FROM pg_database d
                     WHERE d.datname = current_database()) AS owns_database
            FROM pg_roles r WHERE r.rolname = current_user
            """
        )
    ).one()
    problems = []
    if row.rolsuper:
        problems.append("is a superuser")
    if row.rolcreaterole:
        problems.append("can create roles")
    if row.rolcreatedb:
        problems.append("can create databases")
    if row.rolbypassrls:
        problems.append("can bypass row-level security")
    if row.owned_tables:
        problems.append(f"owns {row.owned_tables} table(s)")
    if row.owns_database:
        problems.append("owns the database")
    return problems


def assert_least_privilege(conn: Connection) -> None:
    problems = privilege_problems(conn)
    if problems:
        raise PrivilegedConnectionError(
            "Refusing to run: the app's database user "
            + ", ".join(problems)
            + ". Point DATABASE_URL at the limited 'chopstop_app' user "
            "(MIGRATOR_DATABASE_URL is for Alembic only)."
        )
