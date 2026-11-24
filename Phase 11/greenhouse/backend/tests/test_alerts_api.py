"""HTTP tests of GET /api/alerts with in-memory alerts."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from application.alerts.service import AlertQueryService
from fakes import InMemoryAlerts
from interfaces.api.dependencies import get_alert_service
from main import app

ROW_KEYS = {"id", "location_id", "zone_id", "device_id", "severity", "message",
            "event_type", "status", "created_at"}


def make_client():
    alerts = InMemoryAlerts()
    app.dependency_overrides[get_alert_service] = lambda: AlertQueryService(alerts)
    return TestClient(app), alerts


def teardown_function():
    app.dependency_overrides.clear()


def add(alerts, *, location=None, zone=None, status="active", minutes_ago=0, message="x"):
    row = alerts.insert(location_id=location, zone_id=zone, device_id=uuid4(),
                        severity="warning", message=message, event_type="threshold.crossed")
    row = replace(row, status=status,
                  created_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago))
    alerts.rows[-1] = row
    return row


def test_empty_list():
    client, _ = make_client()
    response = client.get("/api/alerts")
    assert response.status_code == 200
    assert response.json() == []


def test_rows_newest_first_with_the_documented_fields():
    client, alerts = make_client()
    old = add(alerts, minutes_ago=10)
    new = add(alerts, minutes_ago=1)

    body = client.get("/api/alerts").json()

    assert [r["id"] for r in body] == [str(new.id), str(old.id)]
    assert set(body[0]) == ROW_KEYS


def test_default_is_active_and_status_filter_works():
    client, alerts = make_client()
    active = add(alerts)
    resolved = add(alerts, status="resolved")

    assert [r["id"] for r in client.get("/api/alerts").json()] == [str(active.id)]
    assert [r["id"] for r in client.get("/api/alerts", params={"status": "resolved"}).json()] == [str(resolved.id)]
    assert len(client.get("/api/alerts", params={"status": "all"}).json()) == 2
    assert client.get("/api/alerts", params={"status": "open"}).status_code == 400


def test_location_zone_and_since_filters():
    client, alerts = make_client()
    loc, bench1, bench2 = uuid4(), uuid4(), uuid4()
    a = add(alerts, location=loc, zone=bench1, minutes_ago=30)
    b = add(alerts, location=loc, zone=bench1, minutes_ago=1)
    add(alerts, location=loc, zone=bench2)
    add(alerts)  # unassigned

    zone1 = client.get("/api/alerts", params={"zone_id": str(bench1)}).json()
    recent = client.get("/api/alerts", params={
        "zone_id": str(bench1),
        "since": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
    }).json()

    assert [r["id"] for r in zone1] == [str(b.id), str(a.id)]
    assert [r["id"] for r in recent] == [str(b.id)]
    assert len(client.get("/api/alerts", params={"location_id": str(loc)}).json()) == 3


def test_limit_bounds():
    client, alerts = make_client()
    for _ in range(3):
        add(alerts)

    assert len(client.get("/api/alerts", params={"limit": 2}).json()) == 2
    assert client.get("/api/alerts", params={"limit": 0}).status_code == 422
    assert client.get("/api/alerts", params={"limit": 201}).status_code == 422


def test_openapi_documents_alerts():
    schema = TestClient(app).get("/openapi.json").json()

    assert "get" in schema["paths"]["/api/alerts"]
    assert set(schema["components"]["schemas"]["AlertDto"]["properties"]) == ROW_KEYS
