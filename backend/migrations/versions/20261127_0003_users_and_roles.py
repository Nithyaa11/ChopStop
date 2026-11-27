"""users and roles

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-27

Guardrails:
  * role, username format and Argon2id hash format enforced by CHECK constraints
  * the app DB user can't DELETE or TRUNCATE users (deactivate instead)
  * audit_log.actor_user_id must reference a real user
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE = "chopstop_app"  # validated in 0002; same constant


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("failed_login_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("token_version", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "password_changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "left(password_hash, 10) = '$argon2id$'", name=op.f("ck_users_password_is_argon2id")
        ),
        sa.CheckConstraint(
            "role IN ('admin', 'founder', 'cook', 'rider')", name=op.f("ck_users_role_valid")
        ),
        sa.CheckConstraint(
            "username ~ '^[a-z0-9][a-z0-9._-]{2,31}$'", name=op.f("ck_users_username_format")
        ),
        sa.CheckConstraint(
            "failed_login_count >= 0", name=op.f("ck_users_failed_login_count_non_negative")
        ),
        sa.CheckConstraint(
            "length(display_name) BETWEEN 1 AND 80", name=op.f("ck_users_display_name_length")
        ),
        sa.CheckConstraint("token_version >= 0", name=op.f("ck_users_token_version_non_negative")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )

    # Users are deactivated, never deleted (audit history must always point at someone)
    op.execute(f"REVOKE DELETE, TRUNCATE ON users FROM {ROLE}")

    op.create_foreign_key(
        op.f("fk_audit_log_actor_user_id_users"),
        "audit_log",
        "users",
        ["actor_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_audit_log_actor_user_id_users"), "audit_log", type_="foreignkey")
    op.drop_table("users")
