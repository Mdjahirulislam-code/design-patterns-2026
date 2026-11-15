"""HTTP tests of the Phase 5 routes. Repositories are replaced by in-memory fakes."""

from uuid import uuid4

from fastapi.testclient import TestClient

from application.readings.sampling import SamplingService
from application.readings.service import ReadingIngest
from fakes import InMemoryDevices, InMemoryReadings, make_sensor
from infrastructure.adapters.sensors.selector import select_sensor_port
from interfaces.api.dependencies import get_reading_ingest, get_sampling_service
from main import app


def make_client(*devices):
    repo = InMemoryDevices(list(devices))
    readings = InMemoryReadings()
    app.dependency_overrides[get_reading_ingest] = lambda: ReadingIngest(
        repo, readings, select_sensor_port
    )
    app.dependency_overrides[get_sampling_service] = lambda: SamplingService(repo)
    return TestClient(app), readings, repo


def teardown_function():
    app.dependency_overrides.clear()


def test_read_returns_normalized_dto_and_appends_rows():
    sensor = make_sensor("moisture_sensor")
    client, readings, _ = make_client(sensor)

    first = client.post(f"/api/sensors/{sensor.id}/read")
    second = client.post(f"/api/sensors/{sensor.id}/read")

    assert first.status_code == 201
    assert second.status_code == 201
    body = first.json()
    assert set(body) == {"device_id", "value", "unit", "source", "recorded_at"}
    assert body["device_id"] == str(sensor.id)
    assert body["unit"] == "vwc"
    assert body["source"] == "simulation"
    assert 0.2 <= body["value"] <= 0.6
    assert readings.count_for(sensor.id) == 2


def test_read_missing_device_is_404():
    client, _, _ = make_client()
    response = client.post(f"/api/sensors/{uuid4()}/read")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_read_adapter_failure_is_400():
    mqtt = make_sensor(protocol="mqtt", family="edge")
    client, readings, _ = make_client(mqtt)

    response = client.post(f"/api/sensors/{mqtt.id}/read")

    assert response.status_code == 400
    assert response.json()["detail"]
    assert readings.rows == []


def test_list_readings_honours_limit():
    sensor = make_sensor("light_sensor")
    client, _, _ = make_client(sensor)
    for _ in range(3):
        client.post(f"/api/sensors/{sensor.id}/read")

    latest = client.get(f"/api/sensors/{sensor.id}/readings", params={"limit": 1})
    everything = client.get(f"/api/sensors/{sensor.id}/readings")

    assert latest.status_code == 200
    assert len(latest.json()) == 1
    assert latest.json()[0]["source"] == "simulation"
    assert len(everything.json()) == 3


def test_list_readings_missing_device_is_404():
    client, _, _ = make_client()
    assert client.get(f"/api/sensors/{uuid4()}/readings").status_code == 404


def test_patch_sampling_round_trips():
    sensor = make_sensor(interval=300, tracking=True)
    client, _, repo = make_client(sensor)

    response = client.patch(
        f"/api/devices/{sensor.id}/sampling",
        json={"sampling_interval_seconds": 30, "tracking_enabled": False},
    )

    assert response.status_code == 200
    assert response.json() == {
        "device_id": str(sensor.id),
        "sampling_interval_seconds": 30,
        "tracking_enabled": False,
    }
    assert repo.get(sensor.id).sampling_interval_seconds == 30
    assert repo.get(sensor.id).tracking_enabled is False


def test_patch_sampling_below_minimum_is_400():
    sensor = make_sensor(interval=300)
    client, _, repo = make_client(sensor)

    response = client.patch(
        f"/api/devices/{sensor.id}/sampling",
        json={"sampling_interval_seconds": 4, "tracking_enabled": True},
    )

    assert response.status_code == 400
    assert "at least 5" in response.json()["detail"]
    assert repo.get(sensor.id).sampling_interval_seconds == 300


def test_patch_sampling_missing_device_is_404():
    client, _, _ = make_client()
    response = client.patch(
        f"/api/devices/{uuid4()}/sampling",
        json={"sampling_interval_seconds": 30, "tracking_enabled": True},
    )
    assert response.status_code == 404


def test_openapi_documents_phase_5_endpoints():
    schema = TestClient(app).get("/openapi.json").json()

    assert "post" in schema["paths"]["/api/sensors/{sensor_id}/read"]
    assert "get" in schema["paths"]["/api/sensors/{sensor_id}/readings"]
    assert "patch" in schema["paths"]["/api/devices/{device_id}/sampling"]
    reading = schema["components"]["schemas"]["ReadingDto"]["properties"]
    assert set(reading) == {"device_id", "value", "unit", "source", "recorded_at"}
