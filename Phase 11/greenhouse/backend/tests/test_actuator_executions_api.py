"""HTTP tests of the Phase 9 routes with in-memory repositories."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from application.actuators.executions import ActuatorExecutionService
from fakes import (
    InMemoryActuatorStates,
    InMemoryDevices,
    InMemoryExecutionLog,
    make_actuator,
    make_sensor,
)
from infrastructure.adapters.actuators.factory import build_actuator_port
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from interfaces.api.dependencies import get_execution_service
from main import app


def make_client():
    devices = InMemoryDevices()
    states = InMemoryActuatorStates()
    log = InMemoryExecutionLog()
    pump = devices.place(make_actuator("water_pump"))
    sensor = devices.place(make_sensor("moisture_sensor"))
    states.set(pump.id, "idle")

    # the real chain: logging -> max run time -> simulation adapter
    port = build_actuator_port(
        executions=log, states=states, adapter=SimulationActuatorAdapter()
    )
    app.dependency_overrides[get_execution_service] = lambda: ActuatorExecutionService(
        devices, port, log
    )
    return TestClient(app), states, log, pump, sensor


def teardown_function():
    app.dependency_overrides.clear()


def test_executions_start_empty():
    client, _, _, _, _ = make_client()

    response = client.get("/api/actuators/executions")

    assert response.status_code == 200
    assert response.json() == []


def test_apply_success_is_logged_and_listed():
    client, _, _, pump, _ = make_client()

    applied = client.post(f"/api/actuators/{pump.id}/apply", json={"command": "start"})
    listed = client.get("/api/actuators/executions", params={"limit": 20})

    assert applied.status_code == 200
    body = applied.json()
    assert set(body) == {"id", "device_id", "success", "policy_applied", "message", "created_at"}
    assert body["device_id"] == str(pump.id)
    assert body["success"] is True
    assert body["policy_applied"] == ["logging"]
    assert body["message"] is None

    assert listed.status_code == 200
    assert [row["id"] for row in listed.json()] == [body["id"]]


def test_unknown_command_on_idle_actuator_still_succeeds():
    client, _, _, pump, _ = make_client()

    response = client.post(
        f"/api/actuators/{pump.id}/apply", json={"command": "fly_to_the_moon", "payload": {}}
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["policy_applied"] == ["logging"]


def test_blocked_attempt_is_409_and_listed_as_unsuccessful():
    client, states, _, pump, _ = make_client()
    states.set(pump.id, "running", datetime.now(timezone.utc) - timedelta(minutes=31))

    blocked = client.post(f"/api/actuators/{pump.id}/apply", json={"command": "start"})
    rows = client.get("/api/actuators/executions").json()

    assert blocked.status_code == 409
    assert blocked.json()["detail"] == "Max run time exceeded"

    assert len(rows) == 1
    assert rows[0]["device_id"] == str(pump.id)
    assert rows[0]["success"] is False
    assert rows[0]["policy_applied"] == ["maxRunTime", "logging"]
    assert rows[0]["message"] == "Max run time exceeded"


def test_running_for_less_than_30_minutes_is_not_blocked():
    client, states, _, pump, _ = make_client()
    states.set(pump.id, "running", datetime.now(timezone.utc) - timedelta(minutes=5))

    response = client.post(f"/api/actuators/{pump.id}/apply", json={"command": "stop"})

    assert response.status_code == 200


def test_missing_or_non_actuator_is_404_and_not_logged():
    client, _, log, _, sensor = make_client()

    assert client.post(
        f"/api/actuators/{uuid4()}/apply", json={"command": "start"}
    ).status_code == 404
    assert client.post(
        f"/api/actuators/{sensor.id}/apply", json={"command": "start"}
    ).status_code == 404
    assert log.rows == []


def test_empty_command_is_400_and_logged_as_failed():
    client, _, log, pump, _ = make_client()

    response = client.post(f"/api/actuators/{pump.id}/apply", json={"command": "  "})

    assert response.status_code == 400
    assert len(log.rows) == 1
    assert log.rows[0].success is False
    assert log.rows[0].policy_applied == ["logging"]


def test_executions_are_newest_first_and_limited():
    client, _, _, pump, _ = make_client()
    ids = [
        client.post(f"/api/actuators/{pump.id}/apply", json={"command": c}).json()["id"]
        for c in ("start", "stop", "start")
    ]

    two = client.get("/api/actuators/executions", params={"limit": 2}).json()

    assert [row["id"] for row in two] == [ids[2], ids[1]]
    assert client.get("/api/actuators/executions", params={"limit": 0}).status_code == 422


def test_openapi_documents_executions_endpoint():
    schema = TestClient(app).get("/openapi.json").json()

    assert "get" in schema["paths"]["/api/actuators/executions"]
    assert "post" in schema["paths"]["/api/actuators/{device_id}/apply"]
    execution = schema["components"]["schemas"]["ExecutionDto"]["properties"]
    assert set(execution) == {
        "id", "device_id", "success", "policy_applied", "message", "created_at",
    }
