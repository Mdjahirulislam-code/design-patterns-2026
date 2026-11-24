"""HTTP tests of POST/GET /api/commands with in-memory repositories."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from application.commands.service import CommandService
from fakes import (
    InMemoryActuatorStates,
    InMemoryCommandLog,
    InMemoryDevices,
    InMemoryExecutionLog,
    make_actuator,
    make_sensor,
)
from infrastructure.adapters.actuators.factory import build_actuator_port
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from interfaces.api.dependencies import get_command_service
from main import app

ROW_KEYS = {"id", "command_type", "device_id", "payload", "status", "error_message", "created_at"}


def make_client():
    devices = InMemoryDevices()
    states = InMemoryActuatorStates()
    log = InMemoryCommandLog()
    pump = devices.place(make_actuator("water_pump"))
    sensor = devices.place(make_sensor("moisture_sensor"))
    states.set(pump.id, "idle")

    port = build_actuator_port(
        executions=InMemoryExecutionLog(), states=states, adapter=SimulationActuatorAdapter()
    )
    app.dependency_overrides[get_command_service] = lambda: CommandService(
        devices, states, port, log
    )
    return TestClient(app), states, log, pump, sensor


def teardown_function():
    app.dependency_overrides.clear()


def post(client, command_type, device_id, payload=None):
    body = {"command_type": command_type, "device_id": str(device_id)}
    if payload is not None:
        body["payload"] = payload
    return client.post("/api/commands", json=body)


def test_start_pump_is_200_success_and_changes_state():
    client, states, _, pump, _ = make_client()

    response = post(client, "start_pump", pump.id, {})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == ROW_KEYS
    assert (body["command_type"], body["device_id"], body["status"], body["error_message"]) == (
        "start_pump", str(pump.id), "success", None)
    assert states.get(pump.id).state == "running"


def test_rejected_is_409_with_the_row_and_appears_in_history():
    client, states, _, pump, _ = make_client()

    response = post(client, "stop_pump", pump.id)   # idle: not allowed
    history = client.get("/api/commands").json()

    assert response.status_code == 409
    body = response.json()
    assert set(body) == ROW_KEYS
    assert body["status"] == "rejected"
    assert "Cannot stop_pump while the actuator is idle" in body["error_message"]
    assert states.get(pump.id).state == "idle"
    assert [row["id"] for row in history] == [body["id"]]


def test_max_run_time_is_200_failed():
    client, states, _, pump, _ = make_client()
    states.set(pump.id, "running", datetime.now(timezone.utc) - timedelta(minutes=31))

    response = post(client, "stop_pump", pump.id)

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["error_message"] == "Max run time exceeded"
    assert states.get(pump.id).state == "running"


def test_unknown_type_is_400_and_writes_no_row():
    client, _, log, pump, _ = make_client()

    response = post(client, "open_roof", pump.id)

    assert response.status_code == 400
    assert "Unknown command type" in response.json()["detail"]
    assert log.rows == []


def test_missing_or_non_actuator_is_404():
    client, _, log, _, sensor = make_client()

    assert post(client, "start_pump", uuid4()).status_code == 404
    assert post(client, "start_pump", sensor.id).status_code == 404
    assert log.rows == []


def test_set_light_level_defaults_and_bad_level():
    client, _, log, pump, _ = make_client()

    ok = post(client, "set_light_level", pump.id)
    bad = post(client, "set_light_level", pump.id, {"level": "high"})

    assert ok.status_code == 200
    assert ok.json()["payload"] == {"level": 1}
    assert bad.status_code == 400
    assert len(log.rows) == 1


def test_history_is_newest_first_and_limited():
    client, _, _, pump, _ = make_client()
    ids = [post(client, c, pump.id).json()["id"] for c in ("start_pump", "stop_pump", "start_pump")]

    two = client.get("/api/commands", params={"limit": 2}).json()

    assert [row["id"] for row in two] == [ids[2], ids[1]]
    assert client.get("/api/commands", params={"limit": 0}).status_code == 422
    assert client.get("/api/commands", params={"limit": 201}).status_code == 422


def test_openapi_documents_command_endpoints():
    schema = TestClient(app).get("/openapi.json").json()

    assert {"post", "get"} <= set(schema["paths"]["/api/commands"])
    assert set(schema["components"]["schemas"]["CommandLogDto"]["properties"]) == ROW_KEYS
    assert "CommandRequest" in schema["components"]["schemas"]
