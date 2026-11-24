"""Integration: events end as rows in the alerts table (PostgreSQL).

Needs the database from docker compose with `alembic upgrade head` applied.
Skipped when the database (or the Phase 11 table) is not there.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, text

from domain.sensors.reading import Reading
from infrastructure.db import SessionLocal, engine
from infrastructure.persistence.models import (
    ActuatorStateRow,
    AlertRow,
    DeviceRow,
    LocationRow,
    ZoneRow,
)
from infrastructure.sampler_runner import build_reading_ingest
from main import app


def _schema_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1 FROM alerts LIMIT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(
    not _schema_ready(),
    reason="PostgreSQL with the Phase 11 migration is not available",
)


def test_threshold_command_and_state_alerts():
    session = SessionLocal()

    location = LocationRow(name="pytest alerts site")
    session.add(location)
    session.flush()
    bench1 = ZoneRow(location_id=location.id, name="Bench 1",
                     moisture_threshold_low=0.20, moisture_threshold_high=0.45, schedule={})
    bench2 = ZoneRow(location_id=location.id, name="Bench 2",
                     moisture_threshold_low=0.30, moisture_threshold_high=0.60, schedule={})
    session.add_all([bench1, bench2])
    session.flush()

    sensor = DeviceRow(device_type="moisture_sensor", role="sensor", device_family="simulation",
                       display_name="pytest bench1 moisture",
                       default_config={"protocol": "simulation", "unit": "vwc"},
                       zone_id=bench1.id, location_id=location.id, tracking_enabled=True,
                       sampling_interval_seconds=3600)
    quiet = DeviceRow(device_type="moisture_sensor", role="sensor", device_family="simulation",
                      display_name="pytest untracked moisture",
                      default_config={"protocol": "simulation", "unit": "vwc"},
                      zone_id=bench1.id, location_id=location.id, tracking_enabled=False)
    pump = DeviceRow(device_type="water_pump", role="actuator", device_family="simulation",
                     display_name="pytest unassigned pump", default_config={"protocol": "simulation"})
    session.add_all([sensor, quiet, pump])
    session.flush()
    session.add(ActuatorStateRow(device_id=pump.id, state="running",
                                 updated_at=datetime.now(timezone.utc) - timedelta(minutes=31)))
    session.commit()
    ids = {"location": location.id, "bench1": bench1.id, "bench2": bench2.id,
           "sensor": sensor.id, "quiet": quiet.id, "pump": pump.id}

    client = TestClient(app)

    def alerts(**params):
        return client.get("/api/alerts", params={"limit": 200, **params}).json()

    try:
        # 1. a tracked 0.10 reading on Bench 1 (low 0.20) through the one ingest path
        with SessionLocal() as s:
            build_reading_ingest(s).record(
                ids["sensor"], Reading(ids["sensor"], 0.10, "vwc", "mqtt", datetime.now(timezone.utc)))

        bench1_rows = alerts(zone_id=str(ids["bench1"]))
        assert [(r["event_type"], r["severity"], r["message"]) for r in bench1_rows] == [
            ("threshold.crossed", "warning", "Moisture below zone low")]
        assert bench1_rows[0]["location_id"] == str(ids["location"])
        assert bench1_rows[0]["device_id"] == str(ids["sensor"])
        assert alerts(zone_id=str(ids["bench2"])) == []

        # 2. the same reading on an untracked sensor is stored but creates no alert
        with SessionLocal() as s:
            build_reading_ingest(s).record(
                ids["quiet"], Reading(ids["quiet"], 0.05, "vwc", "mqtt", datetime.now(timezone.utc)))
        assert len(alerts(zone_id=str(ids["bench1"]))) == 1

        # 3. failed stop_pump on the unassigned pump: command.failed with null ids
        failed = client.post("/api/commands", json={"command_type": "stop_pump",
                                                    "device_id": str(ids["pump"])})
        assert failed.json()["status"] == "failed"
        pump_rows = [r for r in alerts() if r["device_id"] == str(ids["pump"])]
        assert [(r["event_type"], r["severity"], r["message"], r["location_id"], r["zone_id"])
                for r in pump_rows] == [
            ("command.failed", "warning", "Max run time exceeded", None, None)]

        # 4. transition to error: state.changed, critical
        moved = client.post(f"/api/devices/{ids['pump']}/transition", json={"target": "error"})
        assert moved.status_code == 200
        newest = [r for r in alerts() if r["device_id"] == str(ids["pump"])][0]
        assert (newest["event_type"], newest["severity"], newest["message"]) == (
            "state.changed", "critical", "Actuator entered error")
    finally:
        session.rollback()
        session.execute(delete(AlertRow).where(AlertRow.device_id.in_(
            [ids["sensor"], ids["quiet"], ids["pump"]])))
        for key in ("sensor", "quiet", "pump"):
            session.delete(session.get(DeviceRow, ids[key]))
        session.delete(session.get(LocationRow, ids["location"]))
        session.commit()
        session.close()
