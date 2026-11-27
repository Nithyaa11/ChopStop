"""Write audit log entries. Every consequential change in the app goes through here.

Guardrail: sensitive fields (passwords, hashes, tokens, secrets) are redacted before
they reach the audit log, at any nesting depth.
"""

import re
from typing import Any

from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog

REDACTED = "[REDACTED]"
# Whole words inside a field name, e.g. password_hash, api_key, reset-token, PIN
_SENSITIVE_WORDS = {"password", "passwd", "pwd", "secret", "token", "hash", "otp", "pin"}
_SENSITIVE_SUBSTRINGS = ("password", "apikey", "api_key")


def _is_sensitive(key: str) -> bool:
    k = key.lower()
    words = set(re.split(r"[^a-z0-9]+", k))
    return bool(words & _SENSITIVE_WORDS) or any(s in k for s in _SENSITIVE_SUBSTRINGS)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: REDACTED if _is_sensitive(str(k)) else redact(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [redact(v) for v in value]
    return value


def record(
    session: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str | int | None = None,
    actor_user_id: int | None = None,
    actor_role: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
    request_id: str | None = None,
) -> AuditLog:
    """Add an audit entry to the session. Commits with the caller's transaction,
    so the change and its audit record succeed or fail together."""
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=None if entity_id is None else str(entity_id),
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        before=redact(before) if before is not None else None,
        after=redact(after) if after is not None else None,
        reason=reason,
        request_id=request_id,
    )
    session.add(entry)
    return entry
