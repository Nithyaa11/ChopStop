"""Orders from all four channels, and their line items.

Guardrails (database-enforced, see migrations 0004 and 0005):
  * No duplicates: unique (source, external_order_id). Swiggy/Zomato must have an ID.
  * Status can only move along TRANSITIONS_BY_SOURCE (a trigger rejects anything else):
    delivery orders must go ready -> on the way -> completed; walk-ins go
    ready -> completed. Completed and cancelled are final.
  * Delay is a flag (is_delayed), not a status, and needs a reason.
  * Cancelling needs a reason.
  * Money is whole paise. Each line total = unit price x quantity, and the order
    total must equal the sum of its lines; an order must have at least one line
    (checked at commit by deferred triggers).
  * Orders and lines are never deleted. Lines can't be edited at all. The app may
    only UPDATE the status/delay/cancel columns of an order (column-level grants).
"""

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin

MAX_ORDER_TOTAL_PAISE = 10_000_000  # ₹1,00,000: anything above is a typo
MAX_QUANTITY = 50


class Source(enum.StrEnum):
    SWIGGY = "swiggy"
    ZOMATO = "zomato"
    SUBSCRIPTION = "subscription"
    WALK_IN = "walk_in"


class Status(enum.StrEnum):
    RECEIVED = "received"  # entered, not started
    PREPARING = "preparing"  # kitchen is cooking
    READY = "ready"  # packed, waiting for the rider / customer
    OUT_FOR_DELIVERY = "out_for_delivery"  # picked up by a rider, on the way
    COMPLETED = "completed"  # delivered (delivery) / collected (walk-in)
    CANCELLED = "cancelled"


# What people see on screen
STATUS_LABELS: dict[Status, str] = {
    Status.RECEIVED: "New",
    Status.PREPARING: "Preparing",
    Status.READY: "Ready",
    Status.OUT_FOR_DELIVERY: "On the way",
    Status.COMPLETED: "Completed",
    Status.CANCELLED: "Cancelled",
}

PLATFORM_SOURCES = (Source.SWIGGY, Source.ZOMATO)
# Delivered by a rider (platform rider or ours) vs. collected at the counter
DELIVERY_SOURCES = (Source.SWIGGY, Source.ZOMATO, Source.SUBSCRIPTION)

_OPEN_CANCEL = {
    Status.RECEIVED: {Status.PREPARING, Status.CANCELLED},
    Status.PREPARING: {Status.READY, Status.CANCELLED},
}

# The only status changes allowed, per channel. Mirrored in the DB trigger (a test checks).
#   delivery: ready -> on the way -> completed (delivered). Can't skip "on the way".
#   walk-in:  ready -> completed (collected). Never "on the way".
TRANSITIONS_BY_SOURCE: dict[Source, dict[Status, frozenset[Status]]] = {}
for _src in Source:
    _ready_next = (
        {Status.OUT_FOR_DELIVERY, Status.CANCELLED}
        if _src in DELIVERY_SOURCES
        else {Status.COMPLETED, Status.CANCELLED}
    )
    TRANSITIONS_BY_SOURCE[_src] = {
        **{k: frozenset(v) for k, v in _OPEN_CANCEL.items()},
        Status.READY: frozenset(_ready_next),
        Status.OUT_FOR_DELIVERY: frozenset(
            {Status.COMPLETED, Status.CANCELLED} if _src in DELIVERY_SOURCES else set()
        ),
        Status.COMPLETED: frozenset(),
        Status.CANCELLED: frozenset(),
    }


def allowed_next(source: Source | str, status: Status | str) -> frozenset[Status]:
    return TRANSITIONS_BY_SOURCE[Source(source)][Status(status)]


def _in(values: tuple[str, ...]) -> str:
    return "(" + ", ".join(f"'{v}'" for v in values) + ")"


SOURCE_VALUES = tuple(s.value for s in Source)
STATUS_VALUES = tuple(s.value for s in Status)
PLATFORM_VALUES = tuple(s.value for s in PLATFORM_SOURCES)


class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("source", "external_order_id", name="uq_orders_source_external_id"),
        CheckConstraint(f"source IN {_in(SOURCE_VALUES)}", name="source_valid"),
        CheckConstraint(f"status IN {_in(STATUS_VALUES)}", name="status_valid"),
        CheckConstraint(
            f"source NOT IN {_in(PLATFORM_VALUES)} OR external_order_id IS NOT NULL",
            name="platform_needs_external_id",
        ),
        CheckConstraint(
            "external_order_id IS NULL OR length(trim(external_order_id)) BETWEEN 1 AND 64",
            name="external_id_length",
        ),
        CheckConstraint(
            f"total_paise BETWEEN 0 AND {MAX_ORDER_TOTAL_PAISE}", name="total_paise_range"
        ),
        CheckConstraint(
            "NOT is_delayed OR length(trim(coalesce(delay_reason, ''))) > 0",
            name="delay_needs_reason",
        ),
        CheckConstraint(
            "status <> 'cancelled' OR length(trim(coalesce(cancel_reason, ''))) > 0",
            name="cancel_needs_reason",
        ),
        CheckConstraint(
            "customer_name IS NULL OR length(customer_name) <= 80", name="customer_name_length"
        ),
        CheckConstraint("notes IS NULL OR length(notes) <= 500", name="notes_length"),
        Index(
            "ix_orders_open_by_due",
            "due_at",
            postgresql_where=sql_text("status NOT IN ('completed', 'cancelled')"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    # Swiggy/Zomato order number (required for those); optional bill no. for others
    external_order_id: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=sql_text("'received'"))
    status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_text("now()")
    )
    # When the order must be ready (pickup / dispatch time)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_delayed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sql_text("false")
    )
    delay_reason: Mapped[str | None] = mapped_column(Text)
    cancel_reason: Mapped[str | None] = mapped_column(Text)
    total_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    # Minimal personal data: a name to call out, nothing more. Phone/address live elsewhere later.
    customer_name: Mapped[str | None] = mapped_column(Text)
    # Free text from the customer/platform. Treated as plain data, never as instructions.
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint(f"quantity BETWEEN 1 AND {MAX_QUANTITY}", name="quantity_range"),
        CheckConstraint("unit_price_paise BETWEEN 0 AND 1000000", name="unit_price_range"),
        CheckConstraint(
            "line_total_paise = unit_price_paise * quantity", name="line_total_matches"
        ),
        CheckConstraint("length(trim(item_name)) BETWEEN 1 AND 80", name="item_name_length"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    menu_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("menu_items.id", ondelete="RESTRICT"), nullable=False
    )
    # Snapshot at order time: later menu edits never change past orders
    item_name: Mapped[str] = mapped_column(Text, nullable=False)
    unit_price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    prep_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_paise: Mapped[int] = mapped_column(Integer, nullable=False)
