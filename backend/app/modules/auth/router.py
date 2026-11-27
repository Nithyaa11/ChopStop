"""Login, current user, change own password, log out everywhere."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, SecretStr
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.rate_limit import SlidingWindowLimiter
from app.core.security import WeakPasswordError, verify_password
from app.modules.audit import service as audit
from app.modules.auth.deps import ANY_STAFF, actor_of, public, require_roles
from app.modules.auth.service import LoginFailedError, authenticate
from app.modules.auth.tokens import create_access_token
from app.modules.users import service as users
from app.modules.users.models import User
from app.modules.users.schemas import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

# Per IP: 10 attempts/minute. Per username: 10 attempts/15 minutes (slows guessing
# even from many IPs; the account lockout after 5 wrong passwords still applies).
login_ip_limiter = SlidingWindowLimiter(limit=10, window_seconds=60)
login_user_limiter = SlidingWindowLimiter(limit=10, window_seconds=15 * 60)

LOGIN_FAILED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Wrong username or password, or the account is locked. Try again later.",
    headers={"WWW-Authenticate": "Bearer"},
)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth2 token type label, not a secret
    expires_in: int
    user: UserOut


class ChangePasswordIn(BaseModel):
    current_password: SecretStr
    new_password: SecretStr


def _token_for(user: User) -> TokenOut:
    token, expires_in = create_access_token(
        user_id=user.id, role=user.role, token_version=user.token_version
    )
    return TokenOut(access_token=token, expires_in=expires_in, user=UserOut.model_validate(user))


def _too_many(retry_after: float) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many login attempts. Please wait and try again.",
        headers={"Retry-After": str(int(retry_after))},
    )


@router.post("/login", response_model=TokenOut, dependencies=[Depends(public)])
def login(
    request: Request,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenOut:
    ip = request.client.host if request.client else None
    for limiter, key in (
        (login_ip_limiter, f"ip:{ip}"),
        (login_user_limiter, f"user:{form.username.strip().lower()[:64]}"),
    ):
        wait = limiter.hit(key)
        if wait is not None:
            raise _too_many(wait)

    try:
        user = authenticate(db, username=form.username, password=form.password, ip=ip)
    except LoginFailedError:
        db.commit()  # keep the failure counter + audit entry
        raise LOGIN_FAILED from None
    db.commit()
    db.refresh(user)
    return _token_for(user)


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(require_roles(*ANY_STAFF))]) -> User:
    return user


@router.post("/change-password", response_model=TokenOut)
def change_password(
    body: ChangePasswordIn,
    user: Annotated[User, Depends(require_roles(*ANY_STAFF))],
    db: Annotated[Session, Depends(get_db)],
) -> TokenOut:
    if not verify_password(user.password_hash, body.current_password.get_secret_value()):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is wrong")
    try:
        users.set_password(
            db, actor=actor_of(user), user=user, new_password=body.new_password.get_secret_value()
        )
    except WeakPasswordError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from None
    db.commit()
    db.refresh(user)
    return _token_for(user)  # old tokens are dead; hand back a fresh one


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_everywhere(
    user: Annotated[User, Depends(require_roles(*ANY_STAFF))],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    user.token_version += 1
    audit.record(
        db,
        action="auth.logout_all",
        entity_type="user",
        entity_id=user.id,
        actor_user_id=user.id,
        actor_role=user.role,
    )
    db.commit()
