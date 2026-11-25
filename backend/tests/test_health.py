"""Health endpoint tests, including the "don't leak errors" guardrail."""

from fastapi.testclient import TestClient

from app.main import app, get_db_checker


def test_health_ok_with_real_database(migrated_test_db: str) -> None:
    """Integration: needs `docker compose up -d db` running."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_reports_503_and_leaks_nothing_when_db_down() -> None:
    def broken_db() -> bool:
        raise ConnectionError("could not connect to postgresql://chopstop:SuperSecret@db:5432")

    app.dependency_overrides[get_db_checker] = lambda: broken_db
    try:
        response = TestClient(app).get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unreachable"}
    assert "SuperSecret" not in response.text
    assert "postgresql" not in response.text


def test_cors_rejects_unknown_origin() -> None:
    response = TestClient(app).options(
        "/health",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in response.headers
