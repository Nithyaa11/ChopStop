"""Database-level guardrails for menu, orders and order items.

These tests talk SQL directly as the limited app user, skipping all app code, to prove
the database itself refuses bad data. Everything is rolled back afterwards.
"""

import itertools
import uuid
from collections import deque
from collections.abc import Iterator
from importlib import import_module

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.core.security import hash_password
from app.modules.orders.models import ALLOWED_TRANSITIONS, Status

HASH = hash_password("kitchen-Rush-42")


@pytest.fixture
def conn(app_engine: Engine) -> Iterator[Connection]:
    c = app_engine.connect()
    tx = c.begin()
    try:
        yield c
    finally:
        tx.rollback()
        c.close()


@pytest.fixture
def ids(conn: Connection) -> dict[str, int]:
    """A user (order creator) and a menu item to order."""
    user_id = conn.execute(
        text(
            "INSERT INTO users (username, display_name, role, password_hash) "
            "VALUES (:u, 'T', 'founder', :h) RETURNING id"
        ),
        {"u": f"t{uuid.uuid4().hex[:12]}", "h": HASH},
    ).scalar_one()
    item_id = conn.execute(
        text(
            "INSERT INTO menu_items (name, price_paise, prep_minutes) "
            "VALUES (:n, 24900, 12) RETURNING id"
        ),
        {"n": f"Greek Salad {uuid.uuid4().hex[:6]}"},
    ).scalar_one()
    return {"user": user_id, "item": item_id}


def new_order(
    conn: Connection,
    ids: dict[str, int],
    *,
    source: str = "swiggy",
    external_id: str | None = "auto",
    total: int = 49800,
    lines: list[tuple[int, int, int]] | None = ((24900, 2, 49800),),  # (unit, qty, line_total)
    status: str | None = None,
) -> int:
    ext = f"SWG-{uuid.uuid4().hex[:8]}" if external_id == "auto" else external_id
    order_id = conn.execute(
        text(
            "INSERT INTO orders (source, external_order_id, due_at, total_paise, "
            "created_by_user_id, status) VALUES (:s, :e, now() + interval '30 min', :t, :u, "
            "coalesce(:st, 'received')) RETURNING id"
        ),
        {"s": source, "e": ext, "t": total, "u": ids["user"], "st": status},
    ).scalar_one()
    for unit, qty, line_total in lines or ():
        conn.execute(
            text(
                "INSERT INTO order_items (order_id, menu_item_id, item_name, unit_price_paise, "
                "prep_minutes, quantity, line_total_paise) VALUES (:o, :m, 'Greek Salad', :p, 12, "
                ":q, :lt)"
            ),
            {"o": order_id, "m": ids["item"], "p": unit, "q": qty, "lt": line_total},
        )
    return order_id


def check_now(conn: Connection) -> None:
    """Run the commit-time (deferred) checks immediately."""
    conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))


def set_status(conn: Connection, order_id: int, status: str, reason: str | None = None) -> None:
    conn.execute(
        text(
            "UPDATE orders SET status = :s, cancel_reason = coalesce(:r, cancel_reason) "
            "WHERE id = :i"
        ),
        {"s": status, "r": reason, "i": order_id},
    )


# ---------------- money ----------------


def test_valid_order_passes_all_checks(conn: Connection, ids: dict[str, int]) -> None:
    new_order(conn, ids)
    check_now(conn)


def test_order_without_items_rejected(conn: Connection, ids: dict[str, int]) -> None:
    new_order(conn, ids, lines=None)
    with pytest.raises(DBAPIError, match="has no items"):
        check_now(conn)


def test_total_must_equal_sum_of_lines(conn: Connection, ids: dict[str, int]) -> None:
    new_order(conn, ids, total=10000)  # lines add up to 49800
    with pytest.raises(DBAPIError, match="does not match"):
        check_now(conn)


@pytest.mark.parametrize(
    "line",
    [
        (24900, 2, 40000),  # line total != unit x qty
        (24900, 0, 0),  # zero quantity
        (24900, 51, 24900 * 51),  # absurd quantity
        (-100, 1, -100),  # negative price
    ],
)
def test_bad_lines_rejected(conn: Connection, ids: dict[str, int], line: tuple) -> None:
    with pytest.raises(IntegrityError):
        new_order(conn, ids, total=line[2], lines=[line])


def test_absurd_total_rejected(conn: Connection, ids: dict[str, int]) -> None:
    with pytest.raises(IntegrityError):
        new_order(conn, ids, total=10_000_001, lines=None)


# ---------------- duplicates & channels ----------------


def test_same_swiggy_order_cannot_be_entered_twice(conn: Connection, ids: dict[str, int]) -> None:
    new_order(conn, ids, external_id="SWG-123")
    with pytest.raises(IntegrityError, match="uq_orders_source_external_id"):
        new_order(conn, ids, external_id="SWG-123")


def test_same_number_on_different_platforms_is_fine(conn: Connection, ids: dict[str, int]) -> None:
    new_order(conn, ids, source="swiggy", external_id="12345")
    new_order(conn, ids, source="zomato", external_id="12345")
    check_now(conn)


@pytest.mark.parametrize("source", ["swiggy", "zomato"])
def test_platform_orders_need_their_order_id(
    conn: Connection, ids: dict[str, int], source: str
) -> None:
    with pytest.raises(IntegrityError, match="platform_needs_external_id"):
        new_order(conn, ids, source=source, external_id=None)


def test_walk_ins_dont_need_an_id(conn: Connection, ids: dict[str, int]) -> None:
    new_order(conn, ids, source="walk_in", external_id=None)
    new_order(conn, ids, source="walk_in", external_id=None)
    check_now(conn)


def test_unknown_channel_rejected(conn: Connection, ids: dict[str, int]) -> None:
    with pytest.raises(IntegrityError, match="source_valid"):
        new_order(conn, ids, source="whatsapp")


# ---------------- status steps ----------------


def test_new_orders_must_start_as_received(conn: Connection, ids: dict[str, int]) -> None:
    with pytest.raises(DBAPIError, match="must start as received"):
        new_order(conn, ids, status="completed")


def _path_to(target: Status) -> list[Status]:
    """Shortest allowed path from RECEIVED to target (breadth-first)."""
    queue: deque[list[Status]] = deque([[Status.RECEIVED]])
    while queue:
        path = queue.popleft()
        if path[-1] == target:
            return path[1:]
        queue.extend(path + [n] for n in ALLOWED_TRANSITIONS[path[-1]] if n not in path)
    raise AssertionError(f"{target} unreachable")


@pytest.mark.parametrize(
    ("old", "new"), [(a, b) for a, b in itertools.permutations(Status, 2)], ids=str
)
def test_every_status_change_matches_the_rules(
    conn: Connection, ids: dict[str, int], old: Status, new: Status
) -> None:
    """All 30 possible changes: allowed ones succeed, every other one is refused."""
    order_id = new_order(conn, ids)
    for step in _path_to(old):
        set_status(conn, order_id, step, reason="test" if step == Status.CANCELLED else None)
    allowed = new in ALLOWED_TRANSITIONS[old]
    with conn.begin_nested() as sp:
        try:
            set_status(conn, order_id, new, reason="test")
            ok = True
        except DBAPIError:
            ok = False
            sp.rollback()
    assert ok == allowed, f"{old} -> {new}: expected {'allowed' if allowed else 'refused'}"


def test_status_change_updates_timestamp(conn: Connection, ids: dict[str, int]) -> None:
    order_id = new_order(conn, ids)
    conn.execute(
        text("UPDATE orders SET status_changed_at = now() - interval '1 hour' WHERE id = :i"),
        {"i": order_id},
    )
    before = conn.execute(
        text("SELECT status_changed_at FROM orders WHERE id = :i"), {"i": order_id}
    ).scalar_one()
    set_status(conn, order_id, "preparing")
    after = conn.execute(
        text("SELECT status_changed_at FROM orders WHERE id = :i"), {"i": order_id}
    ).scalar_one()
    assert after > before


def test_cancel_needs_a_reason(conn: Connection, ids: dict[str, int]) -> None:
    order_id = new_order(conn, ids)
    with pytest.raises(IntegrityError, match="cancel_needs_reason"):
        set_status(conn, order_id, "cancelled")


@pytest.mark.parametrize("final", ["completed", "cancelled"])
def test_finished_orders_are_frozen(conn: Connection, ids: dict[str, int], final: str) -> None:
    order_id = new_order(conn, ids)
    for step in _path_to(Status(final)):
        set_status(conn, order_id, step, reason="customer left")
    with pytest.raises(DBAPIError, match="can no longer change"):
        conn.execute(
            text("UPDATE orders SET is_delayed = true, delay_reason = 'x' WHERE id = :i"),
            {"i": order_id},
        )


def test_delay_is_a_flag_alongside_status_and_needs_reason(
    conn: Connection, ids: dict[str, int]
) -> None:
    order_id = new_order(conn, ids)
    set_status(conn, order_id, "preparing")
    with conn.begin_nested() as sp:
        with pytest.raises(IntegrityError, match="delay_needs_reason"):
            conn.execute(text("UPDATE orders SET is_delayed = true WHERE id = :i"), {"i": order_id})
        sp.rollback()
    conn.execute(
        text("UPDATE orders SET is_delayed = true, delay_reason = 'rush' WHERE id = :i"),
        {"i": order_id},
    )
    row = conn.execute(
        text("SELECT status, is_delayed FROM orders WHERE id = :i"), {"i": order_id}
    ).one()
    assert (row.status, row.is_delayed) == ("preparing", True)


def test_migration_transitions_match_the_app() -> None:
    migration = import_module("migrations.versions.20261128_0004_menu_orders_order_items")
    in_db = {Status(a): {Status(b) for b in bs} for a, bs in migration.TRANSITIONS.items()}
    in_app = {a: set(bs) for a, bs in ALLOWED_TRANSITIONS.items() if bs}
    assert in_db == in_app


# ---------------- privileges: what the app user can't do ----------------


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE orders SET total_paise = 1 WHERE id = :i",  # change the price after the fact
        "UPDATE orders SET source = 'walk_in' WHERE id = :i",  # move it to another channel
        "UPDATE orders SET external_order_id = 'X' WHERE id = :i",  # rewrite the Swiggy ID
        "UPDATE orders SET created_by_user_id = created_by_user_id WHERE id = :i",
        "UPDATE order_items SET quantity = 1 WHERE order_id = :i",  # edit lines
        "DELETE FROM order_items WHERE order_id = :i",
        "DELETE FROM orders WHERE id = :i",
        "DELETE FROM menu_items",
        "TRUNCATE orders CASCADE",
    ],
)
def test_app_user_cannot_tamper_with_orders(
    conn: Connection, ids: dict[str, int], statement: str
) -> None:
    order_id = new_order(conn, ids)
    with pytest.raises(DBAPIError, match="permission denied"):
        conn.execute(text(statement), {"i": order_id})


# ---------------- menu ----------------


@pytest.mark.parametrize(
    ("name", "price", "prep"),
    [
        ("", 100, 10),
        ("Bowl", -1, 10),
        ("Bowl", 1_000_001, 10),
        ("Bowl", 100, 0),
        ("Bowl", 100, 181),
    ],
)
def test_bad_menu_items_rejected(conn: Connection, name: str, price: int, prep: int) -> None:
    with pytest.raises(IntegrityError):
        conn.execute(
            text("INSERT INTO menu_items (name, price_paise, prep_minutes) VALUES (:n, :p, :m)"),
            {"n": name or "   ", "p": price, "m": prep},
        )


def test_menu_names_unique_ignoring_case(conn: Connection) -> None:
    name = f"Paneer Bowl {uuid.uuid4().hex[:6]}"
    conn.execute(
        text("INSERT INTO menu_items (name, price_paise, prep_minutes) VALUES (:n, 100, 10)"),
        {"n": name},
    )
    with pytest.raises(IntegrityError):
        conn.execute(
            text("INSERT INTO menu_items (name, price_paise, prep_minutes) VALUES (:n, 100, 10)"),
            {"n": name.upper()},
        )
