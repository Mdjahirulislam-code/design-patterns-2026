"""HTTP tests of GET /api/locations/{location_id}/overview with in-memory repositories."""

import ast
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from application.automation.service import AutomationService
from application.overview.facade import LocationOverviewFacade
from domain.sensors.reading import Reading
from fakes import InMemoryDevices, InMemoryLocations, InMemoryReadings, InMemoryRules, make_sensor
from interfaces.api.dependencies import get_overview_facade
from main import app


def make_client():
    locations = InMemoryLocations()
    devices = InMemoryDevices()
    readings = InMemoryReadings()
    rules = InMemoryRules()
    service = AutomationService(locations, rules, devices, readings)

    location = locations.add_location("Lab Site A")
    zone1 = locations.add_zone(location, "Bench 1", 0.2, 0.45)
    locations.add_zone(location, "Bench 2", 0.3, 0.6)
    sensor = devices.place(make_sensor("moisture_sensor", zone_id=zone1), location)
    readings.insert(Reading(sensor.id, 0.31, "vwc", "simulation", datetime.now(timezone.utc)))

    app.dependency_overrides[get_overview_facade] = lambda: LocationOverviewFacade(
        locations, devices, readings, rules, service
    )
    return TestClient(app), location, service


def teardown_function():
    app.dependency_overrides.clear()


def test_overview_without_strategy_is_200_with_nulls():
    client, location, _ = make_client()

    response = client.get(f"/api/locations/{location}/overview")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"location", "device_counts", "zones", "strategy_key", "last_recommendation"}
    assert body["location"]["name"] == "Lab Site A"
    assert body["device_counts"] == {"sensor": 1, "actuator": 0}
    assert body["strategy_key"] is None
    assert body["last_recommendation"] is None

    bench1, bench2 = body["zones"]
    assert set(bench1) == {
        "id", "name", "moisture_threshold_low", "moisture_threshold_high",
        "devices", "latest_readings",
    }
    assert set(bench1["devices"][0]) == {
        "id", "device_type", "role", "display_name", "state", "allowed_commands",
    }
    assert set(bench1["latest_readings"][0]) == {
        "device_id", "value", "unit", "recorded_at", "tracking_enabled",
        "sampling_interval_seconds",
    }
    assert (bench2["devices"], bench2["latest_readings"]) == ([], [])


def test_overview_with_saved_strategy_has_recommendation():
    client, location, service = make_client()
    service.set_strategy(location, "conservative")

    body = client.get(f"/api/locations/{location}/overview").json()

    assert body["strategy_key"] == "conservative"
    # Bench 1: 0.31 is inside 0.20–0.45, Bench 2 has no sensor -> both wait
    assert body["last_recommendation"] == {
        "action": "wait",
        "reason": "All 2 zones can wait",
    }


def test_missing_location_is_404():
    client, _, _ = make_client()

    response = client.get(f"/api/locations/{uuid4()}/overview")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_openapi_documents_overview_schema():
    schema = TestClient(app).get("/openapi.json").json()

    assert "get" in schema["paths"]["/api/locations/{location_id}/overview"]
    names = schema["components"]["schemas"]
    assert {"LocationOverviewDto", "OverviewZoneDto", "OverviewReadingDto"} <= set(names)


def test_overview_handler_only_imports_the_facade():
    source = Path(__file__).resolve().parents[1] / "src" / "interfaces" / "api" / "overview.py"
    modules = {
        node.module
        for node in ast.walk(ast.parse(source.read_text()))
        if isinstance(node, ast.ImportFrom)
    }

    assert not any("persistence" in m or "repository" in m for m in modules)
    assert "application.automation.service" not in modules
    assert "application.overview.facade" in modules
