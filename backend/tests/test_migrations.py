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


def test_downgrade_then_upgrade_round_trip(engine: Engine) -> None:
    cfg = alembic_config()
    command.downgrade(cfg, "base")
    assert "audit_log" not in inspect(engine).get_table_names()
    command.upgrade(cfg, "head")
    assert "audit_log" in inspect(engine).get_table_names()


def test_models_match_migrations(engine: Engine) -> None:
    """If someone edits a model but forgets the migration, this fails."""
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == [], f"Models and migrations are out of sync: {diff}"
