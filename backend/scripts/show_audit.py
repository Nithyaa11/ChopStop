"""Show the most recent audit log entries (read-only).

Run from backend/:  uv run python -m scripts.show_audit          (last 20)
                    uv run python -m scripts.show_audit 50       (last 50)
Uses the limited app DB user, which can only read and add audit rows, never change them.
"""

import sys

from sqlalchemy import select

from app.core.db import get_sessionmaker
from app.modules.audit.models import AuditLog
from app.modules.users.models import User


def main() -> int:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    limit = max(1, min(limit, 500))
    session = get_sessionmaker()()
    try:
        rows = session.execute(
            select(AuditLog, User.username)
            .outerjoin(User, User.id == AuditLog.actor_user_id)
            .order_by(AuditLog.id.desc())
            .limit(limit)
        ).all()
    finally:
        session.close()
    if not rows:
        print("Audit log is empty.")
        return 0
    print(f"{'id':>5}  {'when (UTC)':19}  {'who':14}  {'action':24}  {'entity':10}  details")
    print("-" * 100)
    for entry, username in reversed(rows):
        who = username or ("system" if entry.actor_role == "system" else "-")
        when = entry.occurred_at.strftime("%Y-%m-%d %H:%M:%S")
        details = entry.after or {}
        if entry.reason:
            details = details | {"reason": entry.reason}
        entity = f"{entry.entity_type}:{entry.entity_id or '-'}"
        print(f"{entry.id:>5}  {when}  {who:14}  {entry.action:24}  {entity:10}  {details}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
