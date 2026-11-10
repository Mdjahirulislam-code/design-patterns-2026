"""HTTP tests of the Phase 6 routes with in-memory repositories."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from application.automation.service import AutomationService
from domain.sensors.reading import Reading
from fakes import InMemoryDevices, InMemoryLocations, InMemoryReadings, InMemoryRules, make_sensor
from interfaces.api.dependencies import get_automation_service
from main import app


def make_client(moisture=0.35):
    locations = InMemoryLocations()
    rules = InMemoryRules()
    devices = InMemoryDevices()
    readings = InMemoryReadings()

    location = locations.add_location()
    zone = locations.add_zone(location, "Zone 1", 0.25, 0.45)
    sensor = make_sensor("moisture_sensor", zone_id=zone)
    devices.devices[sensor.id] = sensor
    readings.insert(Reading(sensor.id, moisture, "vwc", "simulation", datetime.now(timezone.utc)))

    app.dependency_overrides[get_automation_service] = lambda: AutomationService(
        locations, rules, devices, readings
    )
    return TestClient(app), location, rules


def teardown_function():
    app.dependency_overrides.clear()


def test_put_then_evaluate_uses_saved_key():
    client, location, rules = make_client(0.35)

    saved = client.put(f"/api/locations/{location}/automation", json={"strategy_key": "aggressive"})
    evaluated = client.post(f"/api/locations/{location}/automation/evaluate")

    assert saved.status_code == 200
    assert saved.json()["strategy_key"] == "aggressive"
    assert saved.json()["is_default"] is False
    assert rules.get(location).strategy_key == "aggressive"

    assert evaluated.status_code == 200
    body = evaluated.json()
    assert {"location_id", "strategy_key", "action", "reason"} <= set(body)
    assert body["location_id"] == str(location)
    assert body["strategy_key"] == "aggressive"
    assert body["action"] == "irrigate"
    assert len(body["zones"]) == 1


def test_changing_strategy_changes_next_evaluate():
    client, location, _ = make_client(0.35)

    client.put(f"/api/locations/{location}/automation", json={"strategy_key": "conservative"})
    first = client.post(f"/api/locations/{location}/automation/evaluate").json()
    client.put(f"/api/locations/{location}/automation", json={"strategy_key": "aggressive"})
    second = client.post(f"/api/locations/{location}/automation/evaluate").json()

    assert first["action"] == "wait"
    assert first["reason"] == "Moisture 0.35 is within 0.25–0.45"
    assert second["action"] == "irrigate"


def test_get_rule_returns_default_then_saved():
    client, location, _ = make_client()

    before = client.get(f"/api/locations/{location}/automation").json()
    client.put(f"/api/locations/{location}/automation", json={"strategy_key": "aggressive"})
    after = client.get(f"/api/locations/{location}/automation").json()

    assert (before["strategy_key"], before["is_default"]) == ("conservative", True)
    assert (after["strategy_key"], after["is_default"]) == ("aggressive", False)


def test_unknown_key_is_400():
    client, location, rules = make_client()

    response = client.put(f"/api/locations/{location}/automation", json={"strategy_key": "turbo"})

    assert response.status_code == 400
    assert "Unknown strategy" in response.json()["detail"]
    assert rules.get(location) is None


def test_missing_location_is_404():
    client, _, _ = make_client()
    missing = uuid4()

    assert client.put(
        f"/api/locations/{missing}/automation", json={"strategy_key": "aggressive"}
    ).status_code == 404
    assert client.post(f"/api/locations/{missing}/automation/evaluate").status_code == 404
    assert client.get(f"/api/locations/{missing}/automation").status_code == 404


def test_list_strategies_endpoint():
    response = TestClient(app).get("/api/automation/strategies")

    assert response.status_code == 200
    assert [s["key"] for s in response.json()] == ["conservative", "aggressive"]


def test_openapi_documents_automation_endpoints():
    schema = TestClient(app).get("/openapi.json").json()

    assert "put" in schema["paths"]["/api/locations/{location_id}/automation"]
    assert "post" in schema["paths"]["/api/locations/{location_id}/automation/evaluate"]
    names = schema["components"]["schemas"]
    assert {"RecommendationDto", "StrategyUpdateRequest", "AutomationRuleDto"} <= set(names)
