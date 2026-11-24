"""MoistureThresholdSubscriber and AlertPersistenceSubscriber on a real EventBus."""

from datetime import datetime, timezone
from uuid import uuid4

from application.alerts.subscribers import subscribe_alert_handlers
from domain.events.bus import EventBus
from domain.events.events import (
    ActuatorStateChanged,
    AlertCreated,
    CommandFailed,
    ReadingCreated,
    ThresholdCrossed,
)
from fakes import InMemoryAlerts, InMemoryLocations

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)


class World:
    def __init__(self):
        self.locations = InMemoryLocations()
        self.alerts = InMemoryAlerts()
        self.location = self.locations.add_location("Lab Site A")
        self.bench1 = self.locations.add_zone(self.location, "Bench 1", 0.20, 0.45)
        self.bus = subscribe_alert_handlers(EventBus(), self.locations, self.alerts)
        self.seen = []
        for cls in (ThresholdCrossed, AlertCreated):
            self.bus.subscribe(cls, self.seen.append)

    def reading(self, value, unit="vwc", zone=True):
        return ReadingCreated(
            device_id=uuid4(), value=value, unit=unit, source="simulation", recorded_at=NOW,
            location_id=self.location if zone else None, zone_id=self.bench1 if zone else None,
        )


def test_low_moisture_creates_threshold_alert():
    w = World()
    event = w.reading(0.10)

    w.bus.publish(event)

    (row,) = w.alerts.rows
    assert (row.event_type, row.severity, row.message, row.status) == (
        "threshold.crossed", "warning", "Moisture below zone low", "active")
    assert (row.device_id, row.location_id, row.zone_id) == (event.device_id, w.location, w.bench1)
    crossed = [e for e in w.seen if isinstance(e, ThresholdCrossed)]
    assert crossed[0].moisture == 0.10 and crossed[0].threshold_low == 0.20


def test_value_equal_to_low_is_not_below():
    w = World()
    w.bus.publish(w.reading(0.20))
    assert w.alerts.rows == []


def test_value_above_low_creates_nothing():
    w = World()
    w.bus.publish(w.reading(0.35))
    assert w.alerts.rows == []


def test_other_units_are_ignored():
    w = World()
    w.bus.publish(w.reading(0.01, unit="lux"))
    assert w.alerts.rows == []


def test_reading_without_zone_does_not_publish_threshold():
    w = World()
    w.bus.publish(w.reading(0.01, zone=False))
    assert w.alerts.rows == []
    assert w.seen == []


def test_command_failed_is_stored_with_null_ids_for_unassigned_device():
    w = World()
    pump = uuid4()

    w.bus.publish(CommandFailed(pump, None, None, "stop_pump", "Max run time exceeded"))

    (row,) = w.alerts.rows
    assert (row.event_type, row.severity, row.message) == (
        "command.failed", "warning", "Max run time exceeded")
    assert (row.device_id, row.location_id, row.zone_id) == (pump, None, None)


def test_only_error_state_is_stored():
    w = World()
    pump = uuid4()

    w.bus.publish(ActuatorStateChanged(pump, None, None, "idle", "running"))
    w.bus.publish(ActuatorStateChanged(pump, None, None, "running", "idle"))
    assert w.alerts.rows == []

    w.bus.publish(ActuatorStateChanged(pump, None, None, "idle", "error"))

    (row,) = w.alerts.rows
    assert (row.event_type, row.severity, row.message) == (
        "state.changed", "critical", "Actuator entered error")


def test_alert_created_is_published_after_each_insert():
    w = World()
    w.bus.publish(w.reading(0.10))

    created = [e for e in w.seen if isinstance(e, AlertCreated)]
    assert len(created) == 1
    assert created[0].alert_id == w.alerts.rows[0].id
    assert created[0].alert_event_type == "threshold.crossed"
