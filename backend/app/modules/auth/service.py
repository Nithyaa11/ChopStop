"""Login logic.

Guardrails:
  * One generic failure for every reason (unknown user, wrong password, inactive,
    locked), so attackers can't learn which usernames exist.
  * A full password hash check runs even when the user doesn't exist (timing-safe).
  * 5 wrong passwords in a row lock the account for 15 minutes.
  * Every attempt, success or failure, is written to the audit log (never the password).
  * Old hashes are upgraded transparently when the hashing parameters get stronger.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import hash_password, needs_rehash, verify_password
from app.modules.audit import service as audit
from app.modules.users.models import User
from app.modules.users.service import get_by_username

MAX_FAILED_ATTEMPTS = 5
LOCKOUT = timedelta(minutes=15)


class LoginFailedError(Exception):
    """Deliberately vague. Never tell the client *why* login failed."""


def _now() -> datetime:
    return datetime.now(UTC)


def authenticate(session: Session, *, username: str, password: str, ip: str | None) -> User:
    user = get_by_username(session, username) if len(username) <= 64 else None
    password_ok = verify_password(user.password_hash if user else None, password)

    if user is None:
        audit.record(
            session,
            action="auth.login_failed",
            entity_type="user",
            after={"username_attempted": username[:64], "ip": ip, "why": "unknown_user"},
        )
        raise LoginFailedError

    locked = user.locked_until is not None and user.locked_until > _now()
    if locked or not user.is_active or not password_ok:
        why = "locked" if locked else "inactive" if not user.is_active else "wrong_password"
        if why == "wrong_password":
            user.failed_login_count += 1
            if user.failed_login_count >= MAX_FAILED_ATTEMPTS:
                user.locked_until = _now() + LOCKOUT
                user.failed_login_count = 0
                audit.record(
                    session,
                    action="auth.account_locked",
                    entity_type="user",
                    entity_id=user.id,
                    after={"locked_minutes": int(LOCKOUT.total_seconds() // 60), "ip": ip},
                )
        audit.record(
            session,
            action="auth.login_failed",
            entity_type="user",
            entity_id=user.id,
            after={"ip": ip, "why": why},
        )
        raise LoginFailedError

    # Success
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = func.now()
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    audit.record(
        session,
        action="auth.login_succeeded",
        entity_type="user",
        entity_id=user.id,
        actor_user_id=user.id,
        actor_role=user.role,
        after={"ip": ip},
    )
    return user
