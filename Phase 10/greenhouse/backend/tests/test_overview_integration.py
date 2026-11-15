"""Integration: the overview against real rows in PostgreSQL.

Needs the database from docker compose with `alembic upgrade head` applied.
Skipped when the database (or the Phase 6 table) is not there.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from infrastructure.db import SessionLocal, engine
from infrastructure.persistence.models import DeviceRow, LocationRow, ReadingRow, ZoneRow
from main import app


def _schema_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1 FROM automation_rules LIMIT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(
    not _schema_ready(),
    reason="PostgreSQL with the Phase 6 migration is not available",
)


def _device(device_type, role, name, **extra):
    return DeviceRow(
        device_type=device_type,
        role=role,
        device_family="simulation",
        display_name=name,
        default_config={"protocol": "simulation"},
        tracking_enabled=False,  # keep the background sampler away
        **extra,
    )


def test_overview_returns_strategy_and_readings():
    session = SessionLocal()

    location = LocationRow(name="pytest overview site")
    session.add(location)
    session.flush()

    bench1 = ZoneRow(location_id=location.id, name="Bench 1",
                     moisture_threshold_low=0.25, moisture_threshold_high=0.45, schedule={})
    bench2 = ZoneRow(location_id=location.id, name="Bench 2",
                     moisture_threshold_low=0.30, moisture_threshold_high=0.60, schedule={})
    session.add_all([bench1, bench2])
    session.flush()

    sensor = _device("moisture_sensor", "sensor", "pytest bench moisture",
                     zone_id=bench1.id, location_id=location.id, sampling_interval_seconds=45)
    # unassigned: location set but no zone, and no location at all
    loose = _device("moisture_sensor", "sensor", "pytest loose sensor", location_id=location.id)
    spare = _device("water_pump", "actuator", "pytest spare pump")
    session.add_all([sensor, loose, spare])
    session.flush()

    now = datetime.now(timezone.utc)
    session.add_all([
        ReadingRow(device_id=sensor.id, value=Decimal("0.3500"), unit="vwc",
                   source="simulation", recorded_at=now),
        ReadingRow(device_id=loose.id, value=Decimal("0.1000"), unit="vwc",
                   source="simulation", recorded_at=now),
    ])
    session.commit()

    location_id = location.id
    ids = {"sensor": sensor.id, "loose": loose.id, "spare": spare.id}
    bench1_id, bench2_id = bench1.id, bench2.id

    try:
        client = TestClient(app)
        url = f"/api/locations/{location_id}/overview"

        # unknown location -> 404
        assert client.get(f"/api/locations/{uuid4()}/overview").status_code == 404

        # before a key is saved: 200 with both strategy fields null
        response = client.get(url)
        assert response.status_code == 200
        body = response.json()
        assert body["location"]["name"] == "pytest overview site"
        assert body["strategy_key"] is None
        assert body["last_recommendation"] is None

        # counts assigned devices only
        assert body["device_counts"] == {"sensor": 1, "actuator": 0}

        zones = {z["id"]: z for z in body["zones"]}
        assert set(zones) == {str(bench1_id), str(bench2_id)}

        # unassigned devices are absent from every zone
        listed = {d["id"] for z in body["zones"] for d in z["devices"]}
        read = {r["device_id"] for z in body["zones"] for r in z["latest_readings"]}
        assert listed == {str(ids["sensor"])}
        assert str(ids["loose"]) not in listed | read
        assert str(ids["spare"]) not in listed | read

        # the assigned sensor's reading with sampling settings from the device
        (reading,) = zones[str(bench1_id)]["latest_readings"]
        assert reading["device_id"] == str(ids["sensor"])
        assert reading["value"] == 0.35
        assert reading["unit"] == "vwc"
        assert reading["tracking_enabled"] is False
        assert reading["sampling_interval_seconds"] == 45

        # zone with no assigned devices
        assert zones[str(bench2_id)]["devices"] == []
        assert zones[str(bench2_id)]["latest_readings"] == []

        # after saving a key, last_recommendation matches evaluate
        saved = client.put(f"/api/locations/{location_id}/automation",
                           json={"strategy_key": "aggressive"})
        assert saved.status_code == 200

        after = client.get(url).json()
        evaluated = client.post(f"/api/locations/{location_id}/automation/evaluate").json()

        assert after["strategy_key"] == "aggressive"
        assert after["last_recommendation"] == {
            "action": evaluated["action"],
            "reason": evaluated["reason"],
        }
        assert after["last_recommendation"]["action"] == "irrigate"
    finally:
        session.rollback()
        for device_id in ids.values():
            session.delete(session.get(DeviceRow, device_id))  # readings cascade
        session.delete(session.get(LocationRow, location_id))  # zones + rule cascade
        session.commit()
        session.close()
