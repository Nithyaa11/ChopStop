"""Password hashing and password rules (no database needed)."""

import pytest

from app.core.security import (
    MAX_PASSWORD_LENGTH,
    WeakPasswordError,
    check_password_strength,
    hash_password,
    needs_rehash,
    verify_password,
)

GOOD = "kitchen-Rush-42"


def test_hash_is_argon2id_and_not_plaintext() -> None:
    h = hash_password(GOOD)
    assert h.startswith("$argon2id$")
    assert GOOD not in h


def test_same_password_gets_different_hashes() -> None:
    """Random salt: identical passwords don't produce identical hashes."""
    assert hash_password(GOOD) != hash_password(GOOD)


def test_verify_right_and_wrong() -> None:
    h = hash_password(GOOD)
    assert verify_password(h, GOOD)
    assert not verify_password(h, GOOD + "x")
    assert not verify_password(h, "")


def test_verify_unknown_user_is_false() -> None:
    """None = user not found; still runs a full hash check (timing-safe)."""
    assert not verify_password(None, GOOD)


def test_verify_garbage_hash_is_false_not_crash() -> None:
    assert not verify_password("not-a-hash", GOOD)


def test_fresh_hash_does_not_need_rehash() -> None:
    assert not needs_rehash(hash_password(GOOD))


def test_overlong_password_rejected_for_hashing() -> None:
    with pytest.raises(WeakPasswordError):
        hash_password("a" * (MAX_PASSWORD_LENGTH + 1))


@pytest.mark.parametrize(
    "password",
    [
        "short",  # too short
        "password123",  # common
        "aaaaaaaaaaaa",  # no variety
        "ababababab",  # no variety
        "x" * (MAX_PASSWORD_LENGTH + 1),  # too long
    ],
)
def test_weak_passwords_rejected(password: str) -> None:
    with pytest.raises(WeakPasswordError):
        check_password_strength(password)


def test_password_containing_username_rejected() -> None:
    with pytest.raises(WeakPasswordError, match="username"):
        check_password_strength("ravi-kitchen-2026", username="ravi")


def test_good_password_accepted() -> None:
    check_password_strength(GOOD, username="ravi")
