"""status steps depend on the channel (delivery must go via 'on the way')

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-28

Delivery orders (swiggy, zomato, subscription):
    ready -> out_for_delivery ("on the way") -> completed (delivered)
Walk-ins:
    ready -> completed (collected at the counter); never out_for_delivery
Everything else is unchanged from 0004.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen copy of the rules AT THE TIME OF THIS MIGRATION (never import app code here).
# A test checks this equals app.modules.orders.models.TRANSITIONS_BY_SOURCE.
_COMMON = {"received": ("preparing", "cancelled"), "preparing": ("ready", "cancelled")}
_DELIVERY = {
    **_COMMON,
    "ready": ("out_for_delivery", "cancelled"),
    "out_for_delivery": ("completed", "cancelled"),
}
_WALK_IN = {**_COMMON, "ready": ("completed", "cancelled")}
TRANSITIONS = {
    "swiggy": _DELIVERY,
    "zomato": _DELIVERY,
    "subscription": _DELIVERY,
    "walk_in": _WALK_IN,
}

# 0004's rules, restored on downgrade
_OLD_PAIRS = (
    "('received','preparing'),('received','cancelled'),('preparing','ready'),"
    "('preparing','cancelled'),('ready','out_for_delivery'),('ready','completed'),"
    "('ready','cancelled'),('out_for_delivery','completed'),('out_for_delivery','cancelled')"
)


def _function(allowed_condition: str) -> str:
    return f"""
        CREATE OR REPLACE FUNCTION orders_guard_status() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                IF NEW.status <> 'received' THEN
                    RAISE EXCEPTION 'new orders must start as received, not %', NEW.status
                        USING ERRCODE = 'check_violation';
                END IF;
                RETURN NEW;
            END IF;
            IF OLD.status IN ('completed', 'cancelled') THEN
                RAISE EXCEPTION 'order % is % and can no longer change', OLD.id, OLD.status
                    USING ERRCODE = 'check_violation';
            END IF;
            IF NEW.status IS DISTINCT FROM OLD.status THEN
                IF NOT ({allowed_condition}) THEN
                    RAISE EXCEPTION 'status change % -> % is not allowed for % orders',
                        OLD.status, NEW.status, OLD.source
                        USING ERRCODE = 'check_violation';
                END IF;
                NEW.status_changed_at := now();
            END IF;
            RETURN NEW;
        END;
        $$;
    """


def upgrade() -> None:
    triples = ", ".join(
        f"('{src}', '{a}', '{b}')"
        for src, steps in TRANSITIONS.items()
        for a, nexts in steps.items()
        for b in nexts
    )
    op.execute(_function(f"(OLD.source, OLD.status, NEW.status) IN ({triples})"))


def downgrade() -> None:
    op.execute(_function(f"(OLD.status, NEW.status) IN ({_OLD_PAIRS})"))
