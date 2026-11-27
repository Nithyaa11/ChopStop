"""Access tokens (JWT, HS256).

Guardrails:
  * Only HS256 is accepted; "alg: none" and algorithm-switching tricks are rejected.
  * Issuer, audience, expiry, issued-at and subject are all required and checked.
  * Each token carries the user's token_version; bumping it (password change,
    role change, deactivation, "log out everywhere") kills every older token.
  * The role inside the token is NOT trusted for permissions; the live DB role is.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import get_settings

ALGORITHM = "HS256"
ISSUER = "chopstop"
AUDIENCE = "chopstop-api"


class InvalidTokenError(Exception):
    """Token is missing, malformed, expired, or not ours."""


@dataclass(frozen=True)
class TokenClaims:
    user_id: int
    token_version: int


def create_access_token(
    *, user_id: int, role: str, token_version: int, ttl: timedelta | None = None
) -> tuple[str, int]:
    """Return (token, expires_in_seconds)."""
    settings = get_settings()
    lifetime = ttl if ttl is not None else timedelta(minutes=settings.jwt_expire_minutes)
    now = datetime.now(UTC)
    payload = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": str(user_id),
        "role": role,  # informational only (for the frontend)
        "ver": token_version,
        "iat": now,
        "nbf": now,
        "exp": now + lifetime,
        "jti": uuid.uuid4().hex,
        "typ": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=ALGORITHM)
    return token, int(lifetime.total_seconds())


def decode_access_token(token: str) -> TokenClaims:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[ALGORITHM],  # explicit allow-list, never taken from the token
            audience=AUDIENCE,
            issuer=ISSUER,
            leeway=10,
            options={"require": ["exp", "iat", "nbf", "sub", "iss", "aud", "ver", "typ"]},
        )
        if payload.get("typ") != "access":
            raise InvalidTokenError("wrong token type")
        return TokenClaims(user_id=int(payload["sub"]), token_version=int(payload["ver"]))
    except (jwt.PyJWTError, ValueError, TypeError, KeyError) as exc:
        raise InvalidTokenError(str(exc)) from exc
