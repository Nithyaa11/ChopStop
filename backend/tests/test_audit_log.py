"""Guardrail: the audit log is append-only, enforced by the database itself."""

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError


def _insert(engine: Engine, action: str = "order.created") -> int:
    with engine.begin() as conn:
        return conn.execute(
            text(
                "INSERT INTO audit_log (action, entity_type, entity_id, after) "
                "VALUES (:a, 'order', '42', '{\"status\": \"new\"}') RETURNING id"
            ),
            {"a": action},
        ).scalar_one()


def test_insert_allowed_and_timestamped(engine: Engine) -> None:
    row_id = _insert(engine)
    with engine.connect() as conn:
        occurred_at = conn.execute(
            text("SELECT occurred_at FROM audit_log WHERE id = :i"), {"i": row_id}
        ).scalar_one()
    assert occurred_at.tzinfo is not None  # timezone-aware


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE audit_log SET action = 'tampered' WHERE id = :i",
        "DELETE FROM audit_log WHERE id = :i",
    ],
)
def test_update_and_delete_rejected(engine: Engine, statement: str) -> None:
    row_id = _insert(engine)
    with pytest.raises(DBAPIError, match="append-only"), engine.begin() as conn:
        conn.execute(text(statement), {"i": row_id})
    with engine.connect() as conn:
        action = conn.execute(
            text("SELECT action FROM audit_log WHERE id = :i"), {"i": row_id}
        ).scalar_one()
    assert action == "order.created"  # unchanged, still there


def test_truncate_rejected(engine: Engine) -> None:
    _insert(engine)
    with pytest.raises(DBAPIError, match="append-only"), engine.begin() as conn:
        conn.execute(text("TRUNCATE audit_log"))


def test_id_cannot_be_forced(engine: Engine) -> None:
    """IDENTITY ALWAYS: nobody can insert a fake row with a chosen id."""
    with pytest.raises(DBAPIError), engine.begin() as conn:
        conn.execute(text("INSERT INTO audit_log (id, action, entity_type) VALUES (1, 'x', 'y')"))


def test_empty_action_rejected(engine: Engine) -> None:
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text("INSERT INTO audit_log (action, entity_type) VALUES ('', 'order')"))
