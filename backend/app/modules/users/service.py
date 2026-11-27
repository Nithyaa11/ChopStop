"""User management. All account changes go through here.

Guardrails:
  * Only an admin (or the SYSTEM actor used by the one-time CLI bootstrap) may
    create users, change roles, reset passwords or deactivate accounts. Checked
    here as well as at the API layer (defence in depth).
  * Every change writes an audit entry in the same transaction; passwords and
    hashes never appear in it.
  * The last active admin can't be deactivated or demoted (no lock-out).
  * Users are deactivated, never deleted.
  * Password change or deactivation bumps token_version, so existing logins stop working.
"""

import re
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import check_password_strength, hash_password
from app.modules.audit import service as audit
from app.modules.users.models import USERNAME_PATTERN, Role, User


class UserError(ValueError):
    """Message is safe to show to the person making the request."""


class PermissionDeniedError(UserError):
    pass


@dataclass(frozen=True)
class Actor:
    """Who is performing an action."""

    user_id: int | None
    role: str


SYSTEM = Actor(user_id=None, role="system")  # CLI bootstrap only, never exposed over HTTP


def _require_admin(actor: Actor) -> None:
    if actor.role not in (Role.ADMIN.value, SYSTEM.role):
        raise PermissionDeniedError("Only an admin can manage user accounts")


def normalize_username(username: str) -> str:
    name = username.strip().lower()
    if not re.fullmatch(USERNAME_PATTERN, name):
        raise UserError("Username must be 3-32 characters: a-z, 0-9, '.', '_' or '-'")
    return name


def _public(user: User) -> dict[str, object]:
    return {
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
        "is_active": user.is_active,
    }


def _active_admin_count(session: Session) -> int:
    return (
        session.scalar(
            select(func.count()).select_from(User).where(User.role == "admin", User.is_active)
        )
        or 0
    )


def get_by_username(session: Session, username: str) -> User | None:
    return session.scalar(select(User).where(User.username == username.strip().lower()))


def create_user(
    session: Session,
    *,
    actor: Actor,
    username: str,
    display_name: str,
    role: Role | str,
    password: str,
) -> User:
    _require_admin(actor)
    name = normalize_username(username)
    role_value = Role(role).value  # raises ValueError for unknown roles
    display = display_name.strip()
    if not 1 <= len(display) <= 80:
        raise UserError("Display name must be 1-80 characters")
    check_password_strength(password, username=name)
    if get_by_username(session, name) is not None:
        raise UserError("That username is already taken")

    user = User(
        username=name,
        display_name=display,
        role=role_value,
        password_hash=hash_password(password),
    )
    session.add(user)
    session.flush()  # get the id; unique constraint is the final safety net
    audit.record(
        session,
        action="user.created",
        entity_type="user",
        entity_id=user.id,
        actor_user_id=actor.user_id,
        actor_role=actor.role,
        after=_public(user) | {"is_active": True},
    )
    return user


def set_password(session: Session, *, actor: Actor, user: User, new_password: str) -> None:
    """Admin reset, or a user changing their own password."""
    if actor.user_id != user.id:
        _require_admin(actor)
    check_password_strength(new_password, username=user.username)
    user.password_hash = hash_password(new_password)
    user.password_changed_at = func.now()
    user.token_version += 1  # log out existing sessions
    user.failed_login_count = 0
    user.locked_until = None
    audit.record(
        session,
        action="user.password_changed",
        entity_type="user",
        entity_id=user.id,
        actor_user_id=actor.user_id,
        actor_role=actor.role,
    )


def change_role(
    session: Session, *, actor: Actor, user: User, new_role: Role | str, reason: str
) -> None:
    _require_admin(actor)
    new_value = Role(new_role).value
    if not reason.strip():
        raise UserError("A reason is required to change someone's role")
    if user.role == Role.ADMIN.value and new_value != Role.ADMIN.value and user.is_active:
        if _active_admin_count(session) <= 1:
            raise UserError("Can't remove the last active admin")
    before = _public(user)
    user.role = new_value
    user.token_version += 1  # old tokens carry the old role
    audit.record(
        session,
        action="user.role_changed",
        entity_type="user",
        entity_id=user.id,
        actor_user_id=actor.user_id,
        actor_role=actor.role,
        before=before,
        after=_public(user),
        reason=reason.strip(),
    )


def deactivate_user(session: Session, *, actor: Actor, user: User, reason: str) -> None:
    _require_admin(actor)
    if not reason.strip():
        raise UserError("A reason is required to deactivate an account")
    if not user.is_active:
        return
    if user.role == Role.ADMIN.value and _active_admin_count(session) <= 1:
        raise UserError("Can't deactivate the last active admin")
    before = _public(user)
    user.is_active = False
    user.token_version += 1  # log out everywhere
    audit.record(
        session,
        action="user.deactivated",
        entity_type="user",
        entity_id=user.id,
        actor_user_id=actor.user_id,
        actor_role=actor.role,
        before=before,
        after=_public(user),
        reason=reason.strip(),
    )
