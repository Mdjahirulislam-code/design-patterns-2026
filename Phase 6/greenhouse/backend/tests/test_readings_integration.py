"""Integration: POST /read inserts a real row into PostgreSQL.

Needs the database from docker compose with `alembic upgrade head` applied.
The test is skipped when the database (or the Phase 5 table) is not there.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text

from infrastructure.db import SessionLocal, engine
from infrastructure.persistence.models import DeviceRow, ReadingRow
from main import app


def _phase_5_schema_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1 FROM sensor_readings LIMIT 1"))
            connection.execute(text("SELECT tracking_enabled FROM devices LIMIT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(
    not _phase_5_schema_ready(),
    reason="PostgreSQL with the Phase 5 migration is not available",
)


def test_read_inserts_sensor_reading():
    session = SessionLocal()
    device = DeviceRow(
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name="pytest moisture sensor",
        default_config={"protocol": "simulation", "unit": "vwc"},
        # tracking off, so a running sampler cannot add rows during the test
        tracking_enabled=False,
    )
    session.add(device)
    session.commit()
    device_id = device.id

    def row_count() -> int:
        return session.scalar(
            select(func.count()).select_from(ReadingRow).where(ReadingRow.device_id == device_id)
        )

    try:
        client = TestClient(app)
        assert row_count() == 0

        first = client.post(f"/api/sensors/{device_id}/read")
        assert first.status_code == 201
        assert row_count() == 1

        second = client.post(f"/api/sensors/{device_id}/read")
        assert second.status_code == 201
        assert row_count() == 2

        latest = client.get(f"/api/sensors/{device_id}/readings", params={"limit": 1})
        assert latest.status_code == 200
        assert len(latest.json()) == 1
        assert latest.json()[0]["recorded_at"] == second.json()["recorded_at"]
        assert latest.json()[0]["source"] == "simulation"

        stored = session.scalars(
            select(ReadingRow).where(ReadingRow.device_id == device_id)
        ).all()
        assert all(row.unit == "vwc" and row.source == "simulation" for row in stored)
        assert all(0.2 <= float(row.value) <= 0.6 for row in stored)
    finally:
        # readings are removed with the device (ON DELETE CASCADE)
        session.delete(session.get(DeviceRow, device_id))
        session.commit()
        session.close()
