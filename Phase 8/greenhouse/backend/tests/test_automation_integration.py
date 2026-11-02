"""Integration: evaluate against real zones, devices and sensor_readings in PostgreSQL.

Needs the database from docker compose with `alembic upgrade head` applied.
Skipped when the database (or the Phase 6 table) is not there.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from infrastructure.db import SessionLocal, engine
from infrastructure.persistence.models import (
    AutomationRuleRow,
    DeviceRow,
    LocationRow,
    ReadingRow,
    ZoneRow,
)
from main import app


def _phase_6_schema_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1 FROM automation_rules LIMIT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(
    not _phase_6_schema_ready(),
    reason="PostgreSQL with the Phase 6 migration is not available",
)


def test_evaluate_uses_db_readings_zone_thresholds_and_saved_key():
    session = SessionLocal()

    location = LocationRow(name="pytest automation site")
    session.add(location)
    session.flush()

    zone = ZoneRow(
        location_id=location.id,
        name="pytest zone",
        moisture_threshold_low=0.25,
        moisture_threshold_high=0.45,
        schedule={},
    )
    session.add(zone)
    session.flush()

    sensor = DeviceRow(
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name="pytest zone moisture",
        default_config={"protocol": "simulation", "unit": "vwc"},
        zone_id=zone.id,
        location_id=location.id,
        tracking_enabled=False,  # keep the background sampler away
    )
    session.add(sensor)
    session.flush()

    session.add(
        ReadingRow(
            device_id=sensor.id,
            value=Decimal("0.3500"),
            unit="vwc",
            source="simulation",
            recorded_at=datetime.now(timezone.utc),
        )
    )
    session.commit()
    location_id, sensor_id = location.id, sensor.id

    try:
        client = TestClient(app)

        put = client.put(
            f"/api/locations/{location_id}/automation", json={"strategy_key": "conservative"}
        )
        assert put.status_code == 200
        first = client.post(f"/api/locations/{location_id}/automation/evaluate").json()

        client.put(f"/api/locations/{location_id}/automation", json={"strategy_key": "aggressive"})
        second = client.post(f"/api/locations/{location_id}/automation/evaluate").json()

        assert (first["strategy_key"], first["action"]) == ("conservative", "wait")
        assert first["reason"] == "Moisture 0.35 is within 0.25–0.45"
        assert (second["strategy_key"], second["action"]) == ("aggressive", "irrigate")

        rules = session.scalars(
            select(AutomationRuleRow).where(AutomationRuleRow.location_id == location_id)
        ).all()
        assert len(rules) == 1  # upsert, one rule per location
        session.refresh(rules[0])
        assert rules[0].strategy_key == "aggressive"
    finally:
        session.rollback()
        session.delete(session.get(DeviceRow, sensor_id))  # readings cascade
        session.delete(session.get(LocationRow, location_id))  # zones + rule cascade
        session.commit()
        session.close()
