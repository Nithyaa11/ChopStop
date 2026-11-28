"""Authentication and role checks for endpoints. DENY BY DEFAULT.

Every endpoint must declare who may use it:
  * `Depends(require_roles(Role.ADMIN, ...))` for protected endpoints, or
  * `Depends(public)` for the few open ones (health, login).
A test walks every route in the app and fails if any route has neither.

The role is read from the database on every request, never from the token, so a
role change or deactivation takes effect immediately.
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.tokens import InvalidTokenError, decode_access_token
from app.modules.users.models import Role, User
from app.modules.users.service import Actor

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

ROLES_ATTR = "__chopstop_roles__"
PUBLIC_ATTR = "__chopstop_public__"

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not logged in, or your session has expired",
    headers={"WWW-Authenticate": "Bearer"},
)


def public() -> None:
    """Marks an endpoint as intentionally open to everyone."""


setattr(public, PUBLIC_ATTR, True)


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if not token:
        raise _UNAUTHORIZED
    try:
        claims = decode_access_token(token)
    except InvalidTokenError:
        raise _UNAUTHORIZED from None
    user = db.get(User, claims.user_id)
    if user is None or not user.is_active or user.token_version != claims.token_version:
        raise _UNAUTHORIZED
    return user


def require_roles(*roles: Role) -> Callable[..., User]:
    """Allow only the listed roles. An empty list is a programming error."""
    if not roles:
        raise ValueError("require_roles() needs at least one role; use `public` for open routes")
    allowed = frozenset(r.value for r in roles)

    def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your role isn't allowed to do this",
            )
        return user

    setattr(checker, ROLES_ATTR, allowed)
    return checker


ANY_STAFF = (Role.ADMIN, Role.COOK, Role.RIDER)


def actor_of(user: User) -> Actor:
    return Actor(user_id=user.id, role=user.role)
