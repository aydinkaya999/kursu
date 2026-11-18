from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app


def test_health_checks_postgres_and_allows_the_app_origin() -> None:
    settings = Settings()
    with TestClient(create_app(settings)) as client:
        response = client.get("/v1/health", headers={"Origin": settings.app_origin})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["access-control-allow-origin"] == settings.app_origin


def test_health_reports_an_unreachable_database() -> None:
    settings = Settings(database_url="postgresql+psycopg://127.0.0.1:1/kursu")
    with TestClient(create_app(settings)) as client:
        response = client.get("/v1/health")
    assert response.status_code == 503
    assert response.json() == {
        "code": "service_unavailable",
        "message": "Database unavailable",
        "details": {},
    }
