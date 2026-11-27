"""Create a user from the command line (used to bootstrap the first admin).

Run from backend/:  uv run python -m scripts.create_user
The password is typed at a hidden prompt (twice). It is never taken as a
command-line argument, so it can't leak into shell history or process lists.
Runs as the limited app DB user, and is recorded in the audit log as "system".
"""

import getpass
import sys

from app.core.db import get_sessionmaker
from app.core.security import WeakPasswordError
from app.modules.users.models import ROLE_VALUES
from app.modules.users.service import SYSTEM, UserError, create_user


def main() -> int:
    username = input("Username (a-z, 0-9, . _ -): ").strip()
    display_name = input("Display name: ").strip()
    role = input(f"Role {ROLE_VALUES}: ").strip().lower()
    password = getpass.getpass("Password (min 10 chars, hidden): ")
    if getpass.getpass("Repeat password: ") != password:
        print("Passwords don't match. Nothing was created.", file=sys.stderr)
        return 1

    session = get_sessionmaker()()
    try:
        user = create_user(
            session,
            actor=SYSTEM,
            username=username,
            display_name=display_name,
            role=role,
            password=password,
        )
        session.commit()
    except (UserError, WeakPasswordError, ValueError) as exc:
        session.rollback()
        print(f"Not created: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()
    print(f"Created {user.role} '{user.username}' (id {user.id}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
