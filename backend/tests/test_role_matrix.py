"""Who can call what: the full role matrix, checked two ways.

1. The roles declared in code must equal ACCESS below (so a change to permissions
   always shows up as a change to this file, and gets noticed).
2. Over HTTP, every role is tried against every endpoint: allowed roles must get
   past the role check (not 401/403); everyone else must get 403.

When you add an endpoint, add it to ACCESS. The test fails until you do.
"""

import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.main import app
from app.modules.auth import router as auth_router
from app.modules.auth.deps import ROLES_ATTR
from app.modules.users import service
from app.modules.users.models import Role
from tests.test_deny_by_default import _calls, iter_api_routes

A, F, C, R = Role.ADMIN, Role.FOUNDER, Role.COOK, Role.RIDER
EVERYONE = {A, F, C, R}

# ---- THE ROLE MATRIX (single source of truth for permissions) ----
ACCESS: dict[tuple[str, str], set[Role]] = {
    ("GET", "/auth/me"): EVERYONE,
    ("POST", "/auth/change-password"): EVERYONE,
    ("POST", "/auth/logout-all"): EVERYONE,
    ("GET", "/users"): {A},
    ("POST", "/users"): {A},
    ("POST", "/users/{user_id}/role"): {A},
    ("POST", "/users/{user_id}/deactivate"): {A},
    ("POST", "/users/{user_id}/reset-password"): {A},
}

PW = "kitchen-Rush-42"


def declared_roles() -> dict[tuple[str, str], set[str]]:
    out: dict[tuple[str, str], set[str]] = {}
    for prefix, route in iter_api_routes(app.routes):
        roles: set[str] = set()
        for call in _calls(route.dependant):
            roles |= set(getattr(call, ROLES_ATTR, ()))
        if roles:
            for method in route.methods - {"HEAD", "OPTIONS"}:
                out[(method, prefix + route.path)] = roles
    return out


def test_code_matches_the_matrix() -> None:
    expected = {k: {r.value for r in v} for k, v in ACCESS.items()}
    assert declared_roles() == expected


# ---------- HTTP checks ----------


@pytest.fixture(scope="module")
def tokens(migrated_test_db: None, request: pytest.FixtureRequest) -> Iterator[dict[Role, str]]:
    """One user + token per role, inside a transaction rolled back after the module."""
    engine: Engine = request.getfixturevalue("app_engine_module")
    conn = engine.connect()
    outer = conn.begin()
    db = Session(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    out: dict[Role, str] = {}
    for role in Role:
        user = service.create_user(
            db,
            actor=service.SYSTEM,
            username=f"m{role.value}{uuid.uuid4().hex[:8]}",
            display_name=role.value,
            role=role,
            password=PW,
        )
        db.commit()
        auth_router.login_ip_limiter.reset()
        r = client.post("/auth/login", data={"username": user.username, "password": PW})
        out[role] = r.json()["access_token"]
    try:
        yield out
    finally:
        app.dependency_overrides.clear()
        db.close()
        outer.rollback()
        conn.close()


@pytest.fixture(scope="module")
def app_engine_module(migrated_test_db: None) -> Iterator[Engine]:
    from sqlalchemy import create_engine

    from tests.conftest import APP_URL, FAST_FAIL

    eng = create_engine(APP_URL, connect_args=FAST_FAIL)
    yield eng
    eng.dispose()


# Harmless calls: bodies are deliberately invalid and ids don't exist, so an allowed
# role gets 404/422 (past the role check) and nothing is changed.
SAFE_CALLS = {
    ("GET", "/auth/me"): {},
    ("POST", "/auth/change-password"): {"json": {}},
    ("POST", "/auth/logout-all"): None,  # would log the user out: checked separately below
    ("GET", "/users"): {},
    ("POST", "/users"): {"json": {}},
    ("POST", "/users/{user_id}/role"): {"json": {}},
    ("POST", "/users/{user_id}/deactivate"): {"json": {}},
    ("POST", "/users/{user_id}/reset-password"): {"json": {}},
}

CASES = [
    (method, path, role)
    for (method, path), kwargs in SAFE_CALLS.items()
    if kwargs is not None
    for role in Role
]


def test_every_endpoint_has_a_safe_call() -> None:
    assert set(SAFE_CALLS) == set(ACCESS)


@pytest.mark.parametrize(("method", "path", "role"), CASES, ids=lambda v: str(v))
def test_role_gets_in_or_gets_403(
    tokens: dict[Role, str], method: str, path: str, role: Role
) -> None:
    client = TestClient(app)
    url = path.replace("{user_id}", "999999999")
    headers = {"Authorization": f"Bearer {tokens[role]}"}
    r = client.request(method, url, headers=headers, **SAFE_CALLS[(method, path)])
    if role in ACCESS[(method, path)]:
        assert r.status_code not in (401, 403), f"{role} should be allowed: {r.status_code}"
    else:
        assert r.status_code == 403, f"{role} should be blocked: {r.status_code} {r.text}"


@pytest.mark.parametrize(("method", "path"), list(ACCESS), ids=lambda v: str(v))
def test_no_token_is_401_everywhere(migrated_test_db: None, method: str, path: str) -> None:
    url = path.replace("{user_id}", "999999999")
    assert TestClient(app).request(method, url).status_code == 401
