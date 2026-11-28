"""roles: admin, cook, rider (founder role removed)

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-28

Mom and Aunt are the founders and both are admins with full access, so a separate
"founder" role isn't needed. Guardrail: this migration REFUSES to run if any user
still has the founder role. It never silently turns founders into admins, because
that would hand out account-management rights without anyone deciding to.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM users WHERE role = 'founder') THEN
                RAISE EXCEPTION 'Some users still have the founder role. Change them to '
                    'admin/cook/rider first (decide per person), then run this migration.';
            END IF;
        END
        $$;
        """
    )
    op.drop_constraint(op.f("ck_users_role_valid"), "users", type_="check")
    op.create_check_constraint(
        op.f("ck_users_role_valid"), "users", "role IN ('admin', 'cook', 'rider')"
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_users_role_valid"), "users", type_="check")
    op.create_check_constraint(
        op.f("ck_users_role_valid"), "users", "role IN ('admin', 'founder', 'cook', 'rider')"
    )
