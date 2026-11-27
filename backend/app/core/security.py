"""Password hashing (Argon2id) and password rules.

Guardrails:
  * Only Argon2id hashes are ever stored; plaintext never touches the database or logs.
  * verify_password() takes the same time whether or not the user exists
    (use verify_password(None, pw)), so attackers can't probe for valid usernames.
  * needs_rehash() lets login upgrade old hashes when we strengthen the parameters.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# RFC 9106 "low memory" profile: Argon2id, t=3, m=64 MiB, p=4. Strong, still fast on a tablet.
_hasher = PasswordHasher(time_cost=3, memory_cost=64 * 1024, parallelism=4)

# Hash of a random string, used to burn the same time when the user doesn't exist
_DUMMY_HASH = _hasher.hash("chopstop-dummy-password-for-timing")

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128  # caps hashing cost per request (DoS guard)

# Tiny deny-list of the most common choices; length rule does most of the work
_COMMON = {
    "password",
    "password1",
    "password123",
    "1234567890",
    "12345678910",
    "qwertyuiop",
    "chopstop123",
    "chopstop@123",
    "iloveyou12",
    "admin12345",
}


class WeakPasswordError(ValueError):
    """Password doesn't meet the rules. Message is safe to show the user."""


def check_password_strength(password: str, *, username: str = "") -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise WeakPasswordError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise WeakPasswordError(f"Password must be at most {MAX_PASSWORD_LENGTH} characters")
    lowered = password.lower()
    if lowered in _COMMON:
        raise WeakPasswordError("This password is too common")
    if len(set(password)) < 4:
        raise WeakPasswordError("Password needs more variety (at least 4 different characters)")
    if username and username.lower() in lowered:
        raise WeakPasswordError("Password must not contain the username")


def hash_password(password: str) -> str:
    if len(password) > MAX_PASSWORD_LENGTH:
        raise WeakPasswordError(f"Password must be at most {MAX_PASSWORD_LENGTH} characters")
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    """Constant-effort check. Pass None when the user wasn't found."""
    if len(password) > MAX_PASSWORD_LENGTH:
        password = password[:MAX_PASSWORD_LENGTH]  # still spend the time, will fail
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)
