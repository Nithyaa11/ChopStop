"""Guardrail: DENY BY DEFAULT. Every endpoint must explicitly say who may use it.

Fails if any route has neither `Depends(require_roles(...))` nor `Depends(public)`,
and checks the list of public routes doesn't grow without anyone noticing.
"""

from collections.abc import Iterable, Iterator

from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

from app.main import app
from app.modules.auth.deps import PUBLIC_ATTR, ROLES_ATTR

# Adding a route here is a deliberate, reviewed decision.
EXPECTED_PUBLIC = {("GET", "/health"), ("POST", "/auth/login")}

# FastAPI's own docs pages (disabled in production)
FRAMEWORK_PATHS = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}


def iter_api_routes(routes: Iterable[object], prefix: str = "") -> Iterator[tuple[str, APIRoute]]:
    for r in routes:
        if isinstance(r, APIRoute):
            yield prefix, r
        elif hasattr(r, "original_router"):  # FastAPI >= 0.16x included routers
            yield from iter_api_routes(r.original_router.routes, prefix)


def _calls(dep: Dependant) -> Iterator[object]:
    if dep.call is not None:
        yield dep.call
    for sub in dep.dependencies:
        yield from _calls(sub)


def _access(route: APIRoute) -> str:
    calls = list(_calls(route.dependant))
    if any(getattr(c, ROLES_ATTR, None) for c in calls):
        return "roles"
    if any(getattr(c, PUBLIC_ATTR, False) for c in calls):
        return "public"
    return "NONE"


def _all() -> list[tuple[str, str, str]]:
    out = []
    for prefix, route in iter_api_routes(app.routes):
        path = prefix + route.path
        if path in FRAMEWORK_PATHS:
            continue
        for method in route.methods - {"HEAD", "OPTIONS"}:
            out.append((method, path, _access(route)))
    return out


def test_walker_sees_every_route() -> None:
    """If FastAPI internals change, fail loudly instead of checking nothing."""
    walked = {(m, p) for m, p, _ in _all()}
    documented = {
        (method.upper(), path) for path, ops in app.openapi()["paths"].items() for method in ops
    }
    assert walked == documented
    assert len(walked) >= 9


def test_every_route_declares_access() -> None:
    unguarded = [(m, p) for m, p, access in _all() if access == "NONE"]
    assert unguarded == [], f"Routes with no role check and not marked public: {unguarded}"


def test_public_routes_are_exactly_the_expected_ones() -> None:
    public_routes = {(m, p) for m, p, access in _all() if access == "public"}
    assert public_routes == EXPECTED_PUBLIC


def test_checker_catches_an_unguarded_route() -> None:
    """Prove the guard works: a route without a role check must be flagged."""
    from fastapi import APIRouter, Depends

    from app.modules.auth.deps import public, require_roles
    from app.modules.users.models import Role

    r = APIRouter()

    @r.get("/forgot-to-protect")
    def forgot() -> None: ...

    @r.get("/protected", dependencies=[Depends(require_roles(Role.ADMIN))])
    def protected() -> None: ...

    @r.get("/open", dependencies=[Depends(public)])
    def open_() -> None: ...

    found = {route.path: _access(route) for _, route in iter_api_routes(r.routes)}
    assert found == {"/forgot-to-protect": "NONE", "/protected": "roles", "/open": "public"}
