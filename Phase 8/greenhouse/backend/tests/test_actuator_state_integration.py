"""Integration: actuator state is persisted in actuator_states (PostgreSQL).

Needs the database from docker compose with `alembic upgrade head` applied.
Skipped when the database (or the Phase 8 table) is not there.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from infrastructure.db import SessionLocal, engine
from infrastructure.persistence.models import ActuatorStateRow, DeviceRow
from main import app


def _schema_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1 FROM actuator_states LIMIT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(
    not _schema_ready(),
    reason="PostgreSQL with the Phase 8 migration is not available",
)


def _stored_state(device_id):
    with SessionLocal() as session:
        row = session.get(ActuatorStateRow, device_id)
        return (row.state, row.updated_at) if row else None


def test_illegal_transition_does_not_update_row():
    session = SessionLocal()
    pump = DeviceRow(
        device_type="water_pump",
        role="actuator",
        device_family="simulation",
        display_name="pytest pump",
        default_config={"protocol": "simulation"},
    )
    session.add(pump)
    session.flush()
    session.add(ActuatorStateRow(device_id=pump.id, state="idle"))
    session.commit()
    pump_id = pump.id

    try:
        client = TestClient(app)
        url = f"/api/devices/{pump_id}/transition"

        # legal: idle -> running is written to the table
        ok = client.post(url, json={"target": "running"})
        assert ok.status_code == 200
        assert ok.json()["state"] == "running"
        state, updated_at = _stored_state(pump_id)
        assert state == "running"

        # illegal: running -> maintenance is rejected and the row is untouched
        rejected = client.post(url, json={"target": "maintenance"})
        assert rejected.status_code == 409
        assert _stored_state(pump_id) == (state, updated_at)

        # the device list reads the stored state
        devices = client.get("/api/devices", params={"role": "actuator"}).json()
        listed = next(d for d in devices if d["id"] == str(pump_id))
        assert listed["state"] == "running"
        assert listed["allowed_commands"] == ["stop", "report_fault"]

        # a new request (as after a restart) still sees the stored state
        assert client.get(f"/api/devices/{pump_id}/state").json()["state"] == "running"
    finally:
        session.rollback()
        session.delete(session.get(DeviceRow, pump_id))  # state row cascades
        session.commit()
        session.close()
