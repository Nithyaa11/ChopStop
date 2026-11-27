"""Login API, tokens, lockout, rate limits and role checks.

Each test runs inside a transaction that is rolled back at the end (the API's own
commits become savepoints), so nothing is left in the test database.
"""

import uuid
from collections.abc import Iterator
from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.main import app
from app.modules.audit.models import AuditLog
from app.modules.auth import router as auth_router
from app.modules.auth.tokens import ALGORITHM, AUDIENCE, ISSUER, create_access_token
from app.modules.users import service
from app.modules.users.models import Role, User

PW = "kitchen-Rush-42"


@pytest.fixture
def db(app_engine: Engine) -> Iterator[Session]:
    conn = app_engine.connect()
    outer = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        conn.close()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    auth_router.login_ip_limiter.reset()
    auth_router.login_user_limiter.reset()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def make_user(db: Session, role: Role = Role.COOK) -> User:
    user = service.create_user(
        db,
        actor=service.SYSTEM,
        username=f"t{uuid.uuid4().hex[:12]}",
        display_name="Test",
        role=role,
        password=PW,
    )
    db.commit()
    return user


def login(client: TestClient, username: str, password: str = PW):  # noqa: ANN201
    return client.post("/auth/login", data={"username": username, "password": password})


def token_for(client: TestClient, user: User) -> dict[str, str]:
    r = login(client, user.username)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ---------- login ----------


def test_login_success_returns_token_and_no_hash(client: TestClient, db: Session) -> None:
    user = make_user(db)
    r = login(client, user.username)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["user"]["role"] == "cook"
    assert "argon2" not in r.text and "password" not in r.text
    assert r.headers["cache-control"] == "no-store"
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200 and me.json()["username"] == user.username


def test_all_failures_look_identical(client: TestClient, db: Session) -> None:
    """Unknown user, wrong password and inactive user give the same answer."""
    user = make_user(db)
    inactive = make_user(db)
    inactive.is_active = False
    db.commit()
    answers = [
        login(client, "nobody-here"),
        login(client, user.username, "wrong-password-1"),
        login(client, inactive.username),
    ]
    assert {r.status_code for r in answers} == {401}
    assert len({r.text for r in answers}) == 1


def test_lockout_after_five_wrong_passwords(client: TestClient, db: Session) -> None:
    user = make_user(db)
    for _ in range(5):
        assert login(client, user.username, "wrong-password-1").status_code == 401
    # Now even the RIGHT password is refused while locked
    assert login(client, user.username).status_code == 401
    db.refresh(user)
    assert user.locked_until is not None
    actions = list(db.scalars(select(AuditLog.action).where(AuditLog.entity_id == str(user.id))))
    assert "auth.account_locked" in actions
    assert actions.count("auth.login_failed") >= 6


def test_admin_reset_unlocks(client: TestClient, db: Session) -> None:
    admin = make_user(db, Role.ADMIN)
    headers = token_for(client, admin)
    user = make_user(db)
    for _ in range(5):
        login(client, user.username, "wrong-password-1")
    new_pw = "fresh-Salad-77"
    r = client.post(
        f"/users/{user.id}/reset-password", json={"new_password": new_pw}, headers=headers
    )
    assert r.status_code == 204
    assert login(client, user.username, new_pw).status_code == 200


def test_rate_limit_per_ip(client: TestClient) -> None:
    codes = [login(client, f"someone{i}", "wrong-password-1").status_code for i in range(11)]
    assert codes[:10] == [401] * 10
    assert codes[10] == 429


def test_rate_limit_sets_retry_after(client: TestClient) -> None:
    for _ in range(10):
        login(client, "nobody-here", "x" * 12)
    r = login(client, "nobody-here", "x" * 12)
    assert r.status_code == 429 and int(r.headers["retry-after"]) >= 1


def test_password_never_written_to_audit(client: TestClient, db: Session) -> None:
    user = make_user(db)
    login(client, user.username, "Secret-Guess-123")
    login(client, user.username)
    rows = db.scalars(select(AuditLog).where(AuditLog.entity_id == str(user.id))).all()
    dumped = " ".join(str(r.after) for r in rows)
    assert "Secret-Guess-123" not in dumped and PW not in dumped


# ---------- tokens ----------


def _forge(**overrides: object) -> str:
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "1",
        "ver": 0,
        "typ": "access",
        "iat": 1_700_000_000,
        "nbf": 1_700_000_000,
        "exp": 4_000_000_000,
    } | overrides
    key = overrides.pop("_key", get_settings().jwt_secret.get_secret_value())
    return jwt.encode({k: v for k, v in claims.items() if k != "_key"}, key, algorithm=ALGORITHM)


@pytest.mark.parametrize(
    "bad_token",
    [
        "not-a-jwt",
        "",
        _forge(_key="some-other-secret-that-is-long-enough-32b"),  # wrong signature
        _forge(aud="someone-else"),  # wrong audience
        _forge(iss="evil"),  # wrong issuer
        _forge(typ="refresh"),  # wrong type
        _forge(exp=1_700_000_100),  # expired
        jwt.encode({"sub": "1", "ver": 0}, key="", algorithm="none"),  # alg none
    ],
)
def test_bad_tokens_rejected(client: TestClient, bad_token: str) -> None:
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
    assert r.status_code == 401


def test_expired_real_token_rejected(client: TestClient, db: Session) -> None:
    user = make_user(db)
    token, _ = create_access_token(
        user_id=user.id, role=user.role, token_version=0, ttl=timedelta(seconds=-60)
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_logout_all_kills_old_tokens(client: TestClient, db: Session) -> None:
    user = make_user(db)
    headers = token_for(client, user)
    assert client.post("/auth/logout-all", headers=headers).status_code == 204
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_role_change_takes_effect_immediately(client: TestClient, db: Session) -> None:
    admin = make_user(db, Role.ADMIN)
    admin_h = token_for(client, admin)
    cook = make_user(db)
    cook_h = token_for(client, cook)
    r = client.post(
        f"/users/{cook.id}/role",
        json={"role": "founder", "reason": "new partner"},
        headers=admin_h,
    )
    assert r.status_code == 200
    assert client.get("/auth/me", headers=cook_h).status_code == 401  # must log in again


def test_deactivated_user_token_dies(client: TestClient, db: Session) -> None:
    admin_h = token_for(client, make_user(db, Role.ADMIN))
    rider = make_user(db, Role.RIDER)
    rider_h = token_for(client, rider)
    r = client.post(f"/users/{rider.id}/deactivate", json={"reason": "left"}, headers=admin_h)
    assert r.status_code == 200
    assert client.get("/auth/me", headers=rider_h).status_code == 401


def test_change_own_password(client: TestClient, db: Session) -> None:
    user = make_user(db)
    headers = token_for(client, user)
    wrong = client.post(
        "/auth/change-password",
        json={"current_password": "nope-nope-nope", "new_password": "fresh-Salad-77"},
        headers=headers,
    )
    assert wrong.status_code == 400
    ok = client.post(
        "/auth/change-password",
        json={"current_password": PW, "new_password": "fresh-Salad-77"},
        headers=headers,
    )
    assert ok.status_code == 200
    assert client.get("/auth/me", headers=headers).status_code == 401  # old token dead
    new_h = {"Authorization": f"Bearer {ok.json()['access_token']}"}
    assert client.get("/auth/me", headers=new_h).status_code == 200


# ---------- role checks ----------


def test_no_token_is_401(client: TestClient) -> None:
    assert client.get("/users").status_code == 401
    assert client.get("/auth/me").status_code == 401


@pytest.mark.parametrize("role", [Role.FOUNDER, Role.COOK, Role.RIDER])
def test_non_admins_cannot_manage_users(client: TestClient, db: Session, role: Role) -> None:
    headers = token_for(client, make_user(db, role))
    assert client.get("/users", headers=headers).status_code == 403
    r = client.post(
        "/users",
        json={"username": "sneaky", "display_name": "S", "role": "admin", "password": PW},
        headers=headers,
    )
    assert r.status_code == 403


def test_admin_creates_user_and_audit_names_admin(client: TestClient, db: Session) -> None:
    admin = make_user(db, Role.ADMIN)
    headers = token_for(client, admin)
    name = f"n{uuid.uuid4().hex[:10]}"
    r = client.post(
        "/users",
        json={"username": name, "display_name": "New Cook", "role": "cook", "password": PW},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert "argon2" not in r.text and PW not in r.text
    entry = db.scalars(
        select(AuditLog).where(
            AuditLog.action == "user.created", AuditLog.entity_id == str(r.json()["id"])
        )
    ).one()
    assert entry.actor_user_id == admin.id


def test_weak_password_via_api_is_400(client: TestClient, db: Session) -> None:
    headers = token_for(client, make_user(db, Role.ADMIN))
    r = client.post(
        "/users",
        json={"username": "weakling", "display_name": "W", "role": "cook", "password": "123"},
        headers=headers,
    )
    assert r.status_code == 400


def test_security_headers_present(client: TestClient) -> None:
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["cache-control"] == "no-store"
