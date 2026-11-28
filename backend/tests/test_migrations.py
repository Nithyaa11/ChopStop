"""Migrations: apply cleanly, undo cleanly, and match the models exactly."""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from app.db_models import Base
from tests.conftest import alembic_config


def test_single_migration_head() -> None:  # no DB needed: reads migration files only
    """Two heads means two branches of schema history: must never be merged silently."""
    heads = ScriptDirectory.from_config(alembic_config()).get_heads()
    assert len(heads) == 1


def test_downgrade_then_upgrade_round_trip(owner_engine: Engine) -> None:
    cfg = alembic_config()
    command.downgrade(cfg, "base")
    assert "audit_log" not in inspect(owner_engine).get_table_names()
    command.upgrade(cfg, "head")
    assert "audit_log" in inspect(owner_engine).get_table_names()


def test_models_match_migrations(owner_engine: Engine) -> None:
    """If someone edits a model but forgets the migration, this fails."""
    with owner_engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == [], f"Models and migrations are out of sync: {diff}"


def test_roles_migration_refuses_while_founders_exist(owner_engine: Engine) -> None:
    """0006 must not silently promote founders to admin; it stops and asks for a decision."""
    import pytest
    from sqlalchemy import text

    from app.core.security import hash_password

    cfg = alembic_config()
    command.downgrade(cfg, "0005")
    try:
        with owner_engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO users (username, display_name, role, password_hash) "
                    "VALUES ('old-founder-x', 'Old', 'founder', :h)"
                ),
                {"h": hash_password("kitchen-Rush-42")},
            )
        with pytest.raises(Exception, match="founder role"):
            command.upgrade(cfg, "head")
    finally:
        with owner_engine.begin() as conn:
            conn.execute(text("DELETE FROM users WHERE username = 'old-founder-x'"))
        command.upgrade(cfg, "head")
