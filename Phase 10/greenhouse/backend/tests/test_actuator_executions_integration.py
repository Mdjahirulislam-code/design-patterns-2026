"""Integration: every attempt is stored in actuator_execution_log (PostgreSQL).

Needs the database from docker compose with `alembic upgrade head` applied.
Skipped when the database (or the Phase 9 table) is not there.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from infrastructure.db import SessionLocal, engine
from infrastructure.persistence.models import (
    ActuatorExecutionLogRow,
    ActuatorStateRow,
    DeviceRow,
)
from main import app


def _schema_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1 FROM actuator_execution_log LIMIT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(
    not _schema_ready(),
    reason="PostgreSQL with the Phase 9 migration is not available",
)


def _stored_rows(device_id):
    with SessionLocal() as session:
        rows = session.scalars(
            select(ActuatorExecutionLogRow)
            .where(ActuatorExecutionLogRow.device_id == device_id)
            .order_by(ActuatorExecutionLogRow.created_at)
        ).all()
        return [(row.success, list(row.policy_applied), row.message) for row in rows]


def test_blocked_and_successful_attempts_are_stored():
    session = SessionLocal()
    pump = DeviceRow(
        device_type="water_pump",
        role="actuator",
        device_family="simulation",
        display_name="pytest decorator pump",
        default_config={"protocol": "simulation"},
    )
    session.add(pump)
    session.flush()
    # running for 31 minutes: the max-run-time decorator must block
    session.add(
        ActuatorStateRow(
            device_id=pump.id,
            state="running",
            updated_at=datetime.now(timezone.utc) - timedelta(minutes=31),
        )
    )
    session.commit()
    pump_id = pump.id

    try:
        client = TestClient(app)
        url = f"/api/actuators/{pump_id}/apply"

        # 1. blocked: 409, and a row with success=false and both policy names
        blocked = client.post(url, json={"command": "start"})
        assert blocked.status_code == 409
        assert blocked.json()["detail"] == "Max run time exceeded"
        assert _stored_rows(pump_id) == [
            (False, ["maxRunTime", "logging"], "Max run time exceeded"),
        ]

        # 2. the actuator stops (Phase 8 transition), so it is no longer running
        stopped = client.post(f"/api/devices/{pump_id}/transition", json={"target": "idle"})
        assert stopped.status_code == 200

        # 3. now the same apply succeeds: row with success=true, ["logging"], no message
        applied = client.post(url, json={"command": "start"})
        assert applied.status_code == 200
        assert applied.json()["success"] is True
        assert _stored_rows(pump_id) == [
            (False, ["maxRunTime", "logging"], "Max run time exceeded"),
            (True, ["logging"], None),
        ]

        # 4. the list endpoint reads the table, newest first
        listed = client.get("/api/actuators/executions", params={"limit": 200}).json()
        mine = [row for row in listed if row["device_id"] == str(pump_id)]
        assert [row["success"] for row in mine] == [True, False]
        assert mine[1]["policy_applied"] == ["maxRunTime", "logging"]
        assert mine[1]["message"] == "Max run time exceeded"
    finally:
        session.rollback()
        session.delete(session.get(DeviceRow, pump_id))  # state + log rows cascade
        session.commit()
        session.close()
