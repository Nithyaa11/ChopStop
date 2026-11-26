"""least-privilege grants for the chopstop_app database user

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-26

The app user gets:
  * USAGE on schema public (no CREATE)
  * audit_log: SELECT + INSERT only (no UPDATE/DELETE/TRUNCATE)
  * future tables created by the migrator: SELECT/INSERT/UPDATE/DELETE by default.
    Append-only tables must REVOKE UPDATE, DELETE explicitly in their migration.
"""

import re
from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE = "chopstop_app"  # must match app.core.db_roles.APP_DB_ROLE (checked by a test)
# ROLE is interpolated into SQL below, so it must be a plain identifier (no injection possible)
if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", ROLE):
    raise ValueError(f"Unsafe role name: {ROLE!r}")


def upgrade() -> None:
    # Create the role without login if the setup script hasn't run yet; the script
    # sets LOGIN + password. Roles are cluster-wide, so never dropped on downgrade.
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{ROLE}') THEN
                CREATE ROLE {ROLE} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
            END IF;
        END
        $$;
        """
    )
    # Nobody but the owner may create objects in the schema
    op.execute(f"REVOKE CREATE ON SCHEMA public FROM PUBLIC, {ROLE}")
    op.execute(f"GRANT USAGE ON SCHEMA public TO {ROLE}")

    # Audit log: append-only for the app
    op.execute(f"REVOKE ALL ON audit_log FROM {ROLE}")
    op.execute(f"GRANT SELECT, INSERT ON audit_log TO {ROLE}")

    # Future tables/sequences made by the migrator get normal data access only
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {ROLE}"
    )
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO {ROLE}"
    )


def downgrade() -> None:
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE USAGE, SELECT ON SEQUENCES FROM {ROLE}"
    )
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM {ROLE}"
    )
    op.execute(f"REVOKE ALL ON audit_log FROM {ROLE}")
    op.execute(f"REVOKE USAGE ON SCHEMA public FROM {ROLE}")
