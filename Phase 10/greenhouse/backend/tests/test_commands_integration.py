"""Integration: commands against real tables (PostgreSQL).

Needs the database from docker compose with `alembic upgrade head` applied.
Skipped when the database (or the Phase 10 table) is not there.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from infrastructure.db import SessionLocal, engine
from infrastructure.persistence.models import (
    ActuatorExecutionLogRow,
    ActuatorStateRow,
    CommandLogRow,
    DeviceRow,
)
from main import app


def _schema_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1 FROM command_log LIMIT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(
    not _schema_ready(),
    reason="PostgreSQL with the Phase 10 migration is not available",
)


def _state(device_id):
    with SessionLocal() as session:
        return session.get(ActuatorStateRow, device_id).state


def _command_rows(device_id):
    with SessionLocal() as session:
        rows = session.scalars(
            select(CommandLogRow)
            .where(CommandLogRow.device_id == device_id)
            .order_by(CommandLogRow.created_at)
        ).all()
        return [(row.command_type, row.status) for row in rows]


def _execution_count(device_id):
    with SessionLocal() as session:
        return len(session.scalars(
            select(ActuatorExecutionLogRow).where(ActuatorExecutionLogRow.device_id == device_id)
        ).all())


def test_commands_update_state_and_command_log():
    session = SessionLocal()
    pump = DeviceRow(
        device_type="water_pump",
        role="actuator",
        device_family="simulation",
        display_name="pytest command pump",
        default_config={"protocol": "simulation"},
    )
    session.add(pump)
    session.flush()
    session.add(ActuatorStateRow(device_id=pump.id, state="idle"))
    session.commit()
    pump_id = pump.id

    def post(command_type):
        return TestClient(app).post(
            "/api/commands", json={"command_type": command_type, "device_id": str(pump_id)}
        )

    try:
        # rejected: stop on an idle pump. 409, row written, state unchanged, port not reached
        rejected = post("stop_pump")
        assert rejected.status_code == 409
        assert rejected.json()["status"] == "rejected"
        assert _state(pump_id) == "idle"
        assert _execution_count(pump_id) == 0

        # success: start -> running, command_log + execution log rows
        started = post("start_pump")
        assert started.status_code == 200
        assert started.json()["status"] == "success"
        assert _state(pump_id) == "running"
        assert _execution_count(pump_id) == 1

        # success: stop -> idle
        assert post("stop_pump").json()["status"] == "success"
        assert _state(pump_id) == "idle"

        assert _command_rows(pump_id) == [
            ("stop_pump", "rejected"),
            ("start_pump", "success"),
            ("stop_pump", "success"),
        ]

        # history endpoint reads the table, newest first
        history = TestClient(app).get("/api/commands", params={"limit": 200}).json()
        mine = [row for row in history if row["device_id"] == str(pump_id)]
        assert [row["status"] for row in mine] == ["success", "success", "rejected"]

        # the device list now offers the next legal command
        devices = TestClient(app).get("/api/devices", params={"role": "actuator"}).json()
        listed = next(d for d in devices if d["id"] == str(pump_id))
        assert "start_pump" in listed["allowed_commands"]
        assert "stop_pump" not in listed["allowed_commands"]
    finally:
        session.rollback()
        session.delete(session.get(DeviceRow, pump_id))  # state + logs cascade
        session.commit()
        session.close()
