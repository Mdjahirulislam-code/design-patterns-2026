"""Smoke test: the health endpoint answers and reports a database field."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_ok_or_degraded():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("ok", "degraded")
    assert body["db"] in ("ok", "fail")


def test_swagger_docs_are_disabled():
    assert client.get("/docs").status_code == 404
