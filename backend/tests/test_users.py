"""Users & roles: service rules, database constraints, and the audit trail.

Every test runs in a transaction that is rolled back, so nothing is left behind.
"""

import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.core.security import WeakPasswordError, hash_password, verify_password
from app.modules.audit.models import AuditLog
from app.modules.users import service
from app.modules.users.models import Role, User
from app.modules.users.schemas import UserOut
from app.modules.users.service import SYSTEM, Actor, PermissionDeniedError, UserError

PW = "kitchen-Rush-42"


@pytest.fixture
def session(app_engine: Engine) -> Iterator[Session]:
    """Runs as the limited app user, like the real app. Always rolled back."""
    s = Session(app_engine)
    try:
        yield s
    finally:
        s.rollback()
        s.close()


def uname() -> str:
    return f"t{uuid.uuid4().hex[:12]}"


def make(session: Session, role: Role = Role.COOK, actor: Actor = SYSTEM) -> User:
    return service.create_user(
        session, actor=actor, username=uname(), display_name="Test", role=role, password=PW
    )


def as_actor(user: User) -> Actor:
    return Actor(user_id=user.id, role=user.role)


def audit_for(session: Session, user: User) -> list[AuditLog]:
    return list(
        session.scalars(
            select(AuditLog).where(AuditLog.entity_id == str(user.id)).order_by(AuditLog.id)
        )
    )


# ---------- creating users ----------


def test_create_user_stores_argon2id_hash_not_plaintext(session: Session) -> None:
    user = make(session)
    assert user.password_hash.startswith("$argon2id$")
    assert PW not in user.password_hash
    assert verify_password(user.password_hash, PW)


def test_create_user_writes_audit_without_password(session: Session) -> None:
    user = make(session)
    session.flush()
    (entry,) = audit_for(session, user)
    assert entry.action == "user.created"
    assert entry.actor_role == "system"
    assert entry.after is not None and entry.after["role"] == "cook"
    dumped = str(entry.after) + str(entry.before)
    assert "argon2" not in dumped and PW not in dumped


def test_username_normalised_and_unique_case_insensitive(session: Session) -> None:
    name = uname()
    service.create_user(
        session,
        actor=SYSTEM,
        username=f"  {name.upper()} ",
        display_name="A",
        role="cook",
        password=PW,
    )
    with pytest.raises(UserError, match="taken"):
        service.create_user(
            session, actor=SYSTEM, username=name, display_name="B", role="cook", password=PW
        )


@pytest.mark.parametrize("bad", ["ab", "has space", "UPPER!", "-starts-with-dash", "x" * 40])
def test_bad_usernames_rejected(session: Session, bad: str) -> None:
    with pytest.raises(UserError):
        service.create_user(
            session, actor=SYSTEM, username=bad, display_name="A", role="cook", password=PW
        )


def test_unknown_role_rejected(session: Session) -> None:
    with pytest.raises(ValueError):
        service.create_user(
            session,
            actor=SYSTEM,
            username=uname(),
            display_name="A",
            role="superadmin",
            password=PW,
        )


def test_weak_password_rejected(session: Session) -> None:
    with pytest.raises(WeakPasswordError):
        service.create_user(
            session,
            actor=SYSTEM,
            username=uname(),
            display_name="A",
            role="cook",
            password="password123",
        )


@pytest.mark.parametrize("role", [Role.FOUNDER, Role.COOK, Role.RIDER])
def test_only_admin_can_create_users(session: Session, role: Role) -> None:
    non_admin = make(session, role=role)
    with pytest.raises(PermissionDeniedError):
        make(session, actor=as_actor(non_admin))


def test_admin_can_create_users(session: Session) -> None:
    admin = make(session, role=Role.ADMIN)
    created = make(session, role=Role.RIDER, actor=as_actor(admin))
    (entry,) = audit_for(session, created)
    assert entry.actor_user_id == admin.id and entry.actor_role == "admin"


# ---------- changing users ----------


def test_deactivate_logs_out_and_is_audited(session: Session) -> None:
    admin = make(session, role=Role.ADMIN)
    cook = make(session)
    version = cook.token_version
    with pytest.raises(UserError, match="reason"):
        service.deactivate_user(session, actor=as_actor(admin), user=cook, reason="  ")
    service.deactivate_user(session, actor=as_actor(admin), user=cook, reason="left the job")
    session.flush()
    assert cook.is_active is False
    assert cook.token_version == version + 1
    last = audit_for(session, cook)[-1]
    assert last.action == "user.deactivated" and last.reason == "left the job"
    assert last.before["is_active"] is True and last.after["is_active"] is False


def test_last_admin_cannot_be_deactivated_or_demoted(session: Session) -> None:
    admin = make(session, role=Role.ADMIN)
    me = as_actor(admin)
    with pytest.raises(UserError, match="last active admin"):
        service.deactivate_user(session, actor=me, user=admin, reason="oops")
    with pytest.raises(UserError, match="last active admin"):
        service.change_role(session, actor=me, user=admin, new_role=Role.COOK, reason="oops")
    second = make(session, role=Role.ADMIN)
    service.change_role(session, actor=me, user=second, new_role=Role.FOUNDER, reason="promoted")
    assert second.role == "founder"


def test_role_change_bumps_token_version_and_is_audited(session: Session) -> None:
    admin = make(session, role=Role.ADMIN)
    cook = make(session)
    service.change_role(
        session, actor=as_actor(admin), user=cook, new_role=Role.FOUNDER, reason="new partner"
    )
    session.flush()
    assert cook.token_version == 1
    last = audit_for(session, cook)[-1]
    assert (last.before["role"], last.after["role"]) == ("cook", "founder")


def test_set_password_rules(session: Session) -> None:
    cook = make(session)
    rider = make(session, role=Role.RIDER)
    new = "fresh-Salad-77"
    with pytest.raises(PermissionDeniedError):  # rider can't reset the cook's password
        service.set_password(session, actor=as_actor(rider), user=cook, new_password=new)
    service.set_password(session, actor=as_actor(cook), user=cook, new_password=new)  # own: ok
    session.flush()
    assert verify_password(cook.password_hash, new)
    assert not verify_password(cook.password_hash, PW)
    assert cook.token_version == 1
    assert audit_for(session, cook)[-1].action == "user.password_changed"


# ---------- database-level guardrails (bypassing the service) ----------


def _raw_insert(session: Session, **overrides: str) -> None:
    values = {"u": uname(), "r": "cook", "h": hash_password(PW)} | overrides
    session.execute(
        text(
            "INSERT INTO users (username, display_name, role, password_hash) "
            "VALUES (:u, 'X', :r, :h)"
        ),
        values,
    )
    session.flush()


@pytest.mark.parametrize(
    "overrides",
    [
        {"r": "superadmin"},  # unknown role
        {"h": "kitchen-Rush-42"},  # plaintext password
        {"h": "$2b$12$bcrypt-not-allowed"},  # other hash type
        {"u": "UpperCase"},  # not lowercase
    ],
)
def test_database_rejects_invalid_rows(session: Session, overrides: dict[str, str]) -> None:
    with pytest.raises(IntegrityError):
        _raw_insert(session, **overrides)


def test_app_user_cannot_delete_users(session: Session) -> None:
    user = make(session)
    session.flush()
    with pytest.raises(DBAPIError, match="permission denied"):
        session.execute(text("DELETE FROM users WHERE id = :i"), {"i": user.id})


def test_audit_actor_must_be_real_user(session: Session) -> None:
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "INSERT INTO audit_log (action, entity_type, actor_user_id) "
                "VALUES ('x', 'y', 999999999)"
            )
        )


# ---------- nothing leaks the hash ----------


def test_api_schema_and_repr_never_show_hash(session: Session) -> None:
    user = make(session)
    session.flush()
    assert "password_hash" not in UserOut.model_fields
    assert "argon2" not in UserOut.model_validate(user).model_dump_json()
    assert "argon2" not in repr(user)
