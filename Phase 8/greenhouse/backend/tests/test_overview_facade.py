"""LocationOverviewFacade with in-memory repositories. No database, no HTTP."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from application.automation.service import AutomationService
from application.overview.facade import LocationOverviewFacade
from domain.devices.entity import Device
from domain.locations.errors import LocationNotFoundError
from domain.sensors.reading import Reading
from fakes import (
    InMemoryActuatorStates,
    InMemoryDevices,
    InMemoryLocations,
    InMemoryReadings,
    InMemoryRules,
    make_sensor,
)

T0 = datetime(2026, 10, 20, 9, 0, tzinfo=timezone.utc)


class SpyAutomation:
    """Wraps the real AutomationService and counts evaluate() calls."""

    def __init__(self, service: AutomationService) -> None:
        self.service = service
        self.calls = 0

    def evaluate(self, location_id):
        self.calls += 1
        return self.service.evaluate(location_id)


class World:
    def __init__(self):
        self.locations = InMemoryLocations()
        self.devices = InMemoryDevices()
        self.readings = InMemoryReadings()
        self.rules = InMemoryRules()
        self.service = AutomationService(
            self.locations, self.rules, self.devices, self.readings, clock=lambda: T0
        )
        self.automation = SpyAutomation(self.service)
        self.states = InMemoryActuatorStates()
        self.facade = LocationOverviewFacade(
            self.locations, self.devices, self.readings, self.rules, self.automation,
            self.states,
        )

        # Lab Site A: Zone 1 (sensor with reading + pump without reading), Zone 2 empty
        self.location = self.locations.add_location("Lab Site A")
        self.zone1 = self.locations.add_zone(self.location, "Zone 1", 0.25, 0.45)
        self.zone2 = self.locations.add_zone(self.location, "Zone 2", 0.30, 0.60)

        self.sensor = self.devices.place(
            replace(make_sensor("moisture_sensor", zone_id=self.zone1),
                    sampling_interval_seconds=45, tracking_enabled=False),
            self.location,
        )
        self.pump = self.devices.place(
            Device(uuid4(), "water_pump", "actuator", "simulation", "Sim irrigation pump",
                   {"protocol": "simulation"}, zone_id=self.zone1),
            self.location,
        )
        # unassigned: location set but no zone, and no location at all
        self.loose = self.devices.place(make_sensor("moisture_sensor"), self.location)
        self.spare = self.devices.place(make_sensor("light_sensor"))

        self.reading(self.sensor, 0.35)
        self.reading(self.loose, 0.10)
        self.reading(self.spare, 900.0, unit="lux")

    def reading(self, device, value, at=T0, unit="vwc", source="simulation"):
        self.readings.insert(Reading(device.id, value, unit, source, at))


def zone(overview, zone_id):
    return next(z for z in overview.zones if z.id == zone_id)


def test_missing_location_is_not_found():
    w = World()
    with pytest.raises(LocationNotFoundError):
        w.facade.get_overview(uuid4())


def test_location_and_every_zone_are_listed():
    w = World()
    overview = w.facade.get_overview(w.location)

    assert overview.location.id == w.location
    assert overview.location.name == "Lab Site A"
    assert [z.name for z in overview.zones] == ["Zone 1", "Zone 2"]
    assert (zone(overview, w.zone2).moisture_threshold_low,
            zone(overview, w.zone2).moisture_threshold_high) == (0.30, 0.60)


def test_device_counts_include_assigned_devices_only():
    w = World()
    counts = w.facade.get_overview(w.location).device_counts

    assert (counts.sensor, counts.actuator) == (1, 1)


def test_unassigned_devices_are_absent_everywhere():
    w = World()
    overview = w.facade.get_overview(w.location)

    listed = {d.id for z in overview.zones for d in z.devices}
    read = {r.device_id for z in overview.zones for r in z.latest_readings}
    assert listed == {w.sensor.id, w.pump.id}
    assert w.loose.id not in listed | read
    assert w.spare.id not in listed | read


def test_reading_summary_copies_sampling_settings_from_device():
    w = World()
    readings = zone(w.facade.get_overview(w.location), w.zone1).latest_readings

    assert len(readings) == 1
    r = readings[0]
    assert (r.device_id, r.value, r.unit, r.recorded_at) == (w.sensor.id, 0.35, "vwc", T0)
    assert (r.tracking_enabled, r.sampling_interval_seconds) == (False, 45)


def test_device_without_reading_stays_in_devices_only():
    w = World()
    z1 = zone(w.facade.get_overview(w.location), w.zone1)

    assert w.pump.id in {d.id for d in z1.devices}
    assert w.pump.id not in {r.device_id for r in z1.latest_readings}


def test_empty_zone_has_empty_lists():
    w = World()
    z2 = zone(w.facade.get_overview(w.location), w.zone2)

    assert z2.devices == []
    assert z2.latest_readings == []


def test_no_saved_strategy_gives_nulls_and_skips_evaluate():
    w = World()
    overview = w.facade.get_overview(w.location)

    assert overview.strategy_key is None
    assert overview.last_recommendation is None
    assert w.automation.calls == 0


def test_saved_strategy_recommendation_matches_evaluate():
    w = World()
    w.service.set_strategy(w.location, "aggressive")

    overview = w.facade.get_overview(w.location)
    evaluated = w.service.evaluate(w.location)

    assert overview.strategy_key == "aggressive"
    assert overview.last_recommendation.action == evaluated.action == "irrigate"
    assert overview.last_recommendation.reason == evaluated.reason


def test_next_overview_reflects_new_reading_and_new_strategy():
    w = World()
    w.service.set_strategy(w.location, "conservative")
    first = w.facade.get_overview(w.location)

    w.reading(w.sensor, 0.20, at=T0 + timedelta(minutes=5), source="mqtt")  # any source counts
    w.service.set_strategy(w.location, "aggressive")
    second = w.facade.get_overview(w.location)

    assert first.last_recommendation.action == "wait"
    assert zone(second, w.zone1).latest_readings[0].value == 0.20
    assert second.strategy_key == "aggressive"
    assert second.last_recommendation.action == "irrigate"


def test_newest_reading_wins():
    w = World()
    w.reading(w.sensor, 0.50, at=T0 - timedelta(hours=1))  # older row

    assert zone(w.facade.get_overview(w.location), w.zone1).latest_readings[0].value == 0.35


def test_readings_are_loaded_in_one_call_not_per_device():
    w = World()
    w.facade.get_overview(w.location)

    assert w.readings.bulk_calls == 1


def test_device_whose_zone_is_not_in_this_location_is_ignored():
    w = World()
    other_location = w.locations.add_location("Other site")
    other_zone = w.locations.add_zone(other_location, "Elsewhere", 0.2, 0.4)
    stray = w.devices.place(make_sensor(zone_id=other_zone), w.location)  # inconsistent row

    overview = w.facade.get_overview(w.location)

    assert stray.id not in {d.id for z in overview.zones for d in z.devices}
    assert overview.device_counts.sensor == 1


# ---------------- Phase 8: actuator state on the overview ----------------

def test_overview_devices_show_actuator_state():
    w = World()
    w.states.set(w.pump.id, "running")

    devices = {d.id: d for d in zone(w.facade.get_overview(w.location), w.zone1).devices}

    assert (devices[w.pump.id].state, devices[w.pump.id].allowed_commands) == (
        "running", ["stop", "report_fault"])
    assert (devices[w.sensor.id].state, devices[w.sensor.id].allowed_commands) == (None, [])
    assert w.states.bulk_calls == 1


def test_overview_actuator_without_row_shows_idle():
    w = World()

    devices = {d.id: d for d in zone(w.facade.get_overview(w.location), w.zone1).devices}

    assert devices[w.pump.id].state == "idle"
