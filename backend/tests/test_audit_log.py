"""Guardrail: the audit log is append-only, enforced in two layers by the database.

Layer 1 - privileges: the app user (chopstop_app) only has SELECT + INSERT.
Layer 2 - trigger: even the table owner can't UPDATE/DELETE/TRUNCATE.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError

TAMPERING = [
    "UPDATE audit_log SET action = 'tampered' WHERE id = :i",
    "DELETE FROM audit_log WHERE id = :i",
    "TRUNCATE audit_log",
]


def _insert(engine: Engine, action: str = "order.created") -> int:
    with engine.begin() as conn:
        return conn.execute(
            text(
                "INSERT INTO audit_log (action, entity_type, entity_id, after) "
                "VALUES (:a, 'order', '42', '{\"status\": \"new\"}') RETURNING id"
            ),
            {"a": action},
        ).scalar_one()


def _action_of(engine: Engine, row_id: int) -> str:
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT action FROM audit_log WHERE id = :i"), {"i": row_id}
        ).scalar_one()


def test_app_user_can_insert_and_read(app_engine: Engine) -> None:
    row_id = _insert(app_engine)
    with app_engine.connect() as conn:
        occurred_at = conn.execute(
            text("SELECT occurred_at FROM audit_log WHERE id = :i"), {"i": row_id}
        ).scalar_one()
    assert occurred_at.tzinfo is not None  # timezone-aware


@pytest.mark.parametrize("statement", TAMPERING)
def test_app_user_cannot_tamper(app_engine: Engine, statement: str) -> None:
    """Layer 1: blocked by privileges before the trigger even runs."""
    row_id = _insert(app_engine)
    with pytest.raises(DBAPIError, match="permission denied"), app_engine.begin() as conn:
        conn.execute(text(statement), {"i": row_id})
    assert _action_of(app_engine, row_id) == "order.created"


@pytest.mark.parametrize("statement", TAMPERING)
def test_even_owner_cannot_tamper(owner_engine: Engine, statement: str) -> None:
    """Layer 2: the trigger stops the table owner too."""
    row_id = _insert(owner_engine)
    with pytest.raises(DBAPIError, match="append-only"), owner_engine.begin() as conn:
        conn.execute(text(statement), {"i": row_id})
    assert _action_of(owner_engine, row_id) == "order.created"


def test_id_cannot_be_forced(app_engine: Engine) -> None:
    """IDENTITY ALWAYS: nobody can insert a fake row with a chosen id."""
    with pytest.raises(DBAPIError), app_engine.begin() as conn:
        conn.execute(text("INSERT INTO audit_log (id, action, entity_type) VALUES (1, 'x', 'y')"))


def test_empty_action_rejected(app_engine: Engine) -> None:
    with pytest.raises(IntegrityError), app_engine.begin() as conn:
        conn.execute(text("INSERT INTO audit_log (action, entity_type) VALUES ('', 'order')"))
