"""Users and roles.

Guardrails (enforced by the database, not just the app):
  * role must be one of the known roles
  * username is lowercase, 3-32 chars of a-z 0-9 . _ -, and unique
  * password_hash must be an Argon2id hash (plaintext can't be stored by accident)
  * users are never deleted (the app DB user has no DELETE right); deactivate instead
"""

import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Identity, Integer, Text
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin


class Role(enum.StrEnum):
    """Who can do what (decided 28 Nov 2026 with Nithyaa).

    admin - Mom and Aunt (the founders): everything. Orders, kitchen/food page, menu,
            groceries, accounts, money, reports.
    cook  - hired cook: kitchen screen only (orders to cook, mark preparing/ready).
            No money, no prices, no accounts, no customer contact details.
    rider - the 2 delivery boys: only deliveries assigned to them. Name, address and
            phone of those customers until delivered. No kitchen, no money.
    The helper has no login for now; add a role here (and a migration) if that changes.
    """

    ADMIN = "admin"
    COOK = "cook"
    RIDER = "rider"


ROLE_VALUES = tuple(r.value for r in Role)
USERNAME_PATTERN = r"^[a-z0-9][a-z0-9._-]{2,31}$"


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN (" + ", ".join(f"'{r}'" for r in ROLE_VALUES) + ")", name="role_valid"
        ),
        CheckConstraint(f"username ~ '{USERNAME_PATTERN}'", name="username_format"),
        CheckConstraint("left(password_hash, 10) = '$argon2id$'", name="password_is_argon2id"),
        CheckConstraint("length(display_name) BETWEEN 1 AND 80", name="display_name_length"),
        CheckConstraint("failed_login_count >= 0", name="failed_login_count_non_negative"),
        CheckConstraint("token_version >= 0", name="token_version_non_negative"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sql_text("true")
    )
    # Login protection (used by Day 6 login): lock after repeated failures
    failed_login_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=sql_text("0")
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Bumped on password change / "log out everywhere": old tokens stop working
    token_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=sql_text("0")
    )
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_text("now()")
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:  # never include the hash
        return f"User(id={self.id!r}, username={self.username!r}, role={self.role!r})"
