"""AutomationService with in-memory repositories."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from application.automation.service import AutomationService
from domain.automation.errors import LocationNotFoundError, UnknownStrategyError
from domain.sensors.reading import Reading
from fakes import InMemoryDevices, InMemoryLocations, InMemoryReadings, InMemoryRules, make_sensor

T0 = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)


class World:
    def __init__(self):
        self.locations = InMemoryLocations()
        self.rules = InMemoryRules()
        self.devices = InMemoryDevices()
        self.readings = InMemoryReadings()
        self.service = AutomationService(
            self.locations, self.rules, self.devices, self.readings, clock=lambda: T0
        )

    def sensor(self, device_type="moisture_sensor", zone_id=None):
        device = make_sensor(device_type, zone_id=zone_id)
        self.devices.devices[device.id] = device
        return device

    def reading(self, device, value, at=T0, unit="vwc"):
        self.readings.insert(Reading(device.id, value, unit, "simulation", at))


def one_zone_world(moisture=0.35):
    w = World()
    location = w.locations.add_location()
    zone = w.locations.add_zone(location, "Zone 1", 0.25, 0.45)
    w.reading(w.sensor(zone_id=zone), moisture)
    return w, location, zone


def test_default_strategy_when_nothing_saved():
    w, location, _ = one_zone_world()

    rule = w.service.get_rule(location)
    result = w.service.evaluate(location)

    assert rule.is_default is True
    assert rule.strategy_key == "conservative"
    assert result.strategy_key == "conservative"


def test_set_strategy_persists_and_upserts_one_rule_per_location():
    w, location, _ = one_zone_world()

    w.service.set_strategy(location, "aggressive")
    saved = w.service.set_strategy(location, "conservative")

    assert saved.strategy_key == "conservative"
    assert saved.is_default is False
    assert len(w.rules.rules) == 1
    assert w.rules.get(location).strategy_key == "conservative"


def test_unknown_key_is_rejected_and_nothing_is_saved():
    w, location, _ = one_zone_world()

    with pytest.raises(UnknownStrategyError):
        w.service.set_strategy(location, "turbo")
    assert w.rules.writes == 0


def test_missing_location_is_not_found():
    w = World()
    with pytest.raises(LocationNotFoundError):
        w.service.evaluate(uuid4())
    with pytest.raises(LocationNotFoundError):
        w.service.set_strategy(uuid4(), "aggressive")
    with pytest.raises(LocationNotFoundError):
        w.service.get_rule(uuid4())


def test_evaluate_uses_saved_key_and_changes_with_it_for_same_moisture():
    w, location, zone = one_zone_world(moisture=0.35)

    w.service.set_strategy(location, "conservative")
    first = w.service.evaluate(location)

    w.service.set_strategy(location, "aggressive")
    second = w.service.evaluate(location)

    assert (first.strategy_key, first.action) == ("conservative", "wait")
    assert first.reason == "Moisture 0.35 is within 0.25–0.45"
    assert (second.strategy_key, second.action) == ("aggressive", "irrigate")
    assert second.zones[0].zone_id == zone
    assert second.zones[0].moisture == 0.35
    assert second.evaluated_at == T0


def test_latest_reading_among_zone_sensors_wins():
    w = World()
    location = w.locations.add_location()
    zone = w.locations.add_zone(location, "Zone 1", 0.25, 0.45)
    a = w.sensor(zone_id=zone)
    b = w.sensor(zone_id=zone)
    w.reading(a, 0.50, at=T0 - timedelta(minutes=10))
    w.reading(b, 0.20, at=T0 - timedelta(minutes=5))   # newest
    w.reading(a, 0.40, at=T0 - timedelta(minutes=20))

    result = w.service.evaluate(location)

    assert result.zones[0].moisture == 0.20
    assert result.action == "irrigate"


def test_zone_without_sensor_does_not_borrow_other_readings():
    w = World()
    location = w.locations.add_location()
    dry_zone = w.locations.add_zone(location, "A dry", 0.25, 0.45)
    empty_zone = w.locations.add_zone(location, "B empty", 0.25, 0.45)
    w.reading(w.sensor(zone_id=dry_zone), 0.10)
    w.reading(w.sensor(zone_id=None), 0.10)  # unassigned device

    result = w.service.evaluate(location)
    by_zone = {z.zone_id: z for z in result.zones}

    assert by_zone[dry_zone].action == "irrigate"
    assert by_zone[empty_zone].action == "wait"
    assert by_zone[empty_zone].reason == "No moisture sensor in this zone"
    assert by_zone[empty_zone].moisture is None
    assert result.action == "irrigate"
    assert result.reason == "1 of 2 zones need water: A dry"


def test_light_sensor_is_not_used_as_moisture():
    w = World()
    location = w.locations.add_location()
    zone = w.locations.add_zone(location, "Zone 1", 0.25, 0.45)
    w.reading(w.sensor("light_sensor", zone_id=zone), 900.0, unit="lux")

    result = w.service.evaluate(location)

    assert result.zones[0].reason == "No moisture sensor in this zone"
    assert result.zones[0].light == 900.0


def test_each_zone_uses_its_own_thresholds():
    w = World()
    location = w.locations.add_location()
    wide = w.locations.add_zone(location, "Wide", 0.20, 0.50)
    tight = w.locations.add_zone(location, "Tight", 0.32, 0.40)
    w.reading(w.sensor(zone_id=wide), 0.30)
    w.reading(w.sensor(zone_id=tight), 0.30)

    result = w.service.evaluate(location)  # default conservative
    by_zone = {z.zone_id: z.action for z in result.zones}

    assert by_zone == {wide: "wait", tight: "irrigate"}


def test_location_without_zones_waits():
    w = World()
    location = w.locations.add_location()

    result = w.service.evaluate(location)

    assert (result.action, result.reason, result.zones) == ("wait", "Location has no zones", [])


def test_all_zones_wait_summary():
    w = World()
    location = w.locations.add_location()
    for name in ("Z1", "Z2"):
        zone = w.locations.add_zone(location, name, 0.25, 0.45)
        w.reading(w.sensor(zone_id=zone), 0.40)

    result = w.service.evaluate(location)

    assert (result.action, result.reason) == ("wait", "All 2 zones can wait")


def test_list_strategies():
    keys = [s.key for s in AutomationService.list_strategies()]
    assert keys == ["conservative", "aggressive"]
