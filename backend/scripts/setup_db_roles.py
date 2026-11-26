"""One-time (idempotent) setup: create/update the limited chopstop_app DB user.

Run from backend/:  uv run python -m scripts.setup_db_roles
Then:               uv run alembic upgrade head
Reads DATABASE_URL (app user + password) and MIGRATOR_DATABASE_URL (owner) from .env.
"""

from app.core.config import get_settings
from app.core.db_roles import APP_DB_ROLE, ensure_app_role


def main() -> None:
    settings = get_settings()
    if settings.migrator_database_url is None:
        raise SystemExit("MIGRATOR_DATABASE_URL is not set in .env")
    ensure_app_role(
        settings.migrator_database_url.get_secret_value(),
        settings.database_url.get_secret_value(),
    )
    print(f"OK: database user {APP_DB_ROLE!r} is set up with limited rights.")


if __name__ == "__main__":
    main()
