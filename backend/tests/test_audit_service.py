"""Guardrail: sensitive fields never reach the audit log (no database needed)."""

from app.modules.audit.service import REDACTED, redact


def test_sensitive_keys_redacted_at_any_depth() -> None:
    data = {
        "username": "ravi",
        "password": "hunter2-hunter2",
        "password_hash": "$argon2id$...",
        "nested": {"api_key": "k", "reset-token": "t", "PIN": "1234", "note": "ok"},
        "items": [{"otp": "999999", "qty": 2}],
    }
    out = redact(data)
    assert out["username"] == "ravi"
    assert out["password"] == REDACTED
    assert out["password_hash"] == REDACTED
    assert out["nested"] == {
        "api_key": REDACTED,
        "reset-token": REDACTED,
        "PIN": REDACTED,
        "note": "ok",
    }
    assert out["items"] == [{"otp": REDACTED, "qty": 2}]


def test_ordinary_words_not_over_redacted() -> None:
    """'pin' inside 'shipping', 'hash' inside 'hashtag' must not be hidden."""
    data = {"shipping_address": "x", "hashtag": "#salad", "opinion": "good", "spinach_qty": 3}
    assert redact(data) == data


def test_original_not_modified() -> None:
    data = {"password": "p"}
    redact(data)
    assert data == {"password": "p"}
