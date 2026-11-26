"""Guardrail: the app refuses to start when connected as a powerful DB user."""

import pytest
from sqlalchemy.engine import Engine

import app.main as main
from app.core.db_roles import PrivilegedConnectionError


def test_startup_ok_as_app_user(app_engine: Engine, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "get_engine", lambda: app_engine)
    main.check_database_privileges()  # no error


def test_startup_refused_as_owner(owner_engine: Engine, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "get_engine", lambda: owner_engine)
    with pytest.raises(PrivilegedConnectionError, match="superuser"):
        main.check_database_privileges()
