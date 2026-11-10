"""HTTP tests of the Phase 8 routes with in-memory repositories."""

from uuid import uuid4

from fastapi.testclient import TestClient

from application.actuators.service import ActuatorStateService
from application.devices.queries import DeviceQueryService
from fakes import InMemoryActuatorStates, InMemoryDevices, make_actuator, make_sensor
from interfaces.api.dependencies import get_actuator_state_service, get_device_queries
from main import app


def make_client():
    devices = InMemoryDevices()
    states = InMemoryActuatorStates()
    pump = devices.place(make_actuator("water_pump"))
    sensor = devices.place(make_sensor("moisture_sensor"))
    states.set(pump.id, "idle")

    app.dependency_overrides[get_actuator_state_service] = lambda: ActuatorStateService(devices, states)
    app.dependency_overrides[get_device_queries] = lambda: DeviceQueryService(devices, states)
    return TestClient(app), states, pump, sensor


def teardown_function():
    app.dependency_overrides.clear()


def test_legal_transition_is_200_and_saved():
    client, states, pump, _ = make_client()

    response = client.post(f"/api/devices/{pump.id}/transition", json={"target": "running"})

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "running"
    assert body["allowed_commands"] == ["stop", "report_fault"]
    assert states.get(pump.id).state == "running"


def test_illegal_transition_is_409_and_not_saved():
    client, states, pump, _ = make_client()
    client.post(f"/api/devices/{pump.id}/transition", json={"target": "running"})

    response = client.post(f"/api/devices/{pump.id}/transition", json={"target": "maintenance"})

    assert response.status_code == 409
    assert "Allowed commands: stop, report_fault" in response.json()["detail"]
    assert states.get(pump.id).state == "running"
    assert states.writes == 1


def test_unknown_target_is_400():
    client, states, pump, _ = make_client()

    response = client.post(f"/api/devices/{pump.id}/transition", json={"target": "flying"})

    assert response.status_code == 400
    assert states.writes == 0


def test_missing_or_non_actuator_is_404():
    client, _, _, sensor = make_client()

    assert client.post(f"/api/devices/{uuid4()}/transition", json={"target": "running"}).status_code == 404
    assert client.post(f"/api/devices/{sensor.id}/transition", json={"target": "running"}).status_code == 404
    assert client.get(f"/api/devices/{sensor.id}/state").status_code == 404


def test_get_state():
    client, _, pump, _ = make_client()

    body = client.get(f"/api/devices/{pump.id}/state").json()

    assert body["state"] == "idle"
    assert body["allowed_commands"] == ["start", "power_off", "begin_maintenance", "report_fault"]


def test_device_list_has_state_and_allowed_commands():
    client, _, pump, sensor = make_client()
    client.post(f"/api/devices/{pump.id}/transition", json={"target": "running"})

    by_id = {d["id"]: d for d in client.get("/api/devices").json()}

    assert by_id[str(pump.id)]["state"] == "running"
    assert by_id[str(pump.id)]["allowed_commands"] == ["stop", "report_fault"]
    assert by_id[str(sensor.id)]["state"] is None
    assert by_id[str(sensor.id)]["allowed_commands"] == []


def test_openapi_documents_state_fields_and_transition():
    schema = TestClient(app).get("/openapi.json").json()

    device = schema["components"]["schemas"]["DeviceDto"]["properties"]
    assert {"state", "allowed_commands"} <= set(device)
    assert "post" in schema["paths"]["/api/devices/{device_id}/transition"]
    assert "get" in schema["paths"]["/api/devices/{device_id}/state"]
    assert "TransitionRequest" in schema["components"]["schemas"]
