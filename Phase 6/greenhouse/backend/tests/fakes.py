"""In-memory stand-ins for the repositories, so tests need no database."""

from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID, uuid4

from domain.automation.rule import StrategyRule
from domain.devices.entity import Device
from domain.locations.entity import ZoneThresholds
from domain.sensors.reading import Reading


def make_sensor(
    device_type: str = "moisture_sensor",
    protocol: str = "simulation",
    family: str = "simulation",
    interval: int = 60,
    tracking: bool = True,
    vendor_stub: bool = False,
    zone_id: UUID | None = None,
) -> Device:
    config: dict = {"protocol": protocol}
    if vendor_stub:
        config["vendor_stub"] = True
    return Device(
        id=uuid4(),
        device_type=device_type,
        role="sensor",
        device_family=family,
        display_name=f"Test {device_type}",
        default_config=config,
        sampling_interval_seconds=interval,
        tracking_enabled=tracking,
        zone_id=zone_id,
    )


class InMemoryDevices:
    def __init__(self, devices: list[Device] | None = None) -> None:
        self.devices: dict[UUID, Device] = {d.id: d for d in devices or []}

    def get(self, device_id: UUID) -> Device | None:
        return self.devices.get(device_id)

    def list_sensors(self) -> list[Device]:
        return [d for d in self.devices.values() if d.role == "sensor"]

    def list_sensors_in_zone(self, zone_id: UUID) -> list[Device]:
        return [d for d in self.list_sensors() if d.zone_id == zone_id]

    def update_sampling(
        self, device_id: UUID, sampling_interval_seconds: int, tracking_enabled: bool
    ) -> Device | None:
        device = self.devices.get(device_id)
        if device is None:
            return None
        updated = replace(
            device,
            sampling_interval_seconds=sampling_interval_seconds,
            tracking_enabled=tracking_enabled,
        )
        self.devices[device_id] = updated
        return updated


class InMemoryReadings:
    def __init__(self) -> None:
        self.rows: list[Reading] = []

    def insert(self, reading: Reading) -> Reading:
        self.rows.append(reading)
        return reading

    def list_for_device(self, device_id: UUID, limit: int = 20) -> list[Reading]:
        rows = [r for r in self.rows if r.device_id == device_id]
        rows.sort(key=lambda r: r.recorded_at, reverse=True)
        return rows[:limit]

    def latest_for_device(self, device_id: UUID) -> Reading | None:
        rows = self.list_for_device(device_id, limit=1)
        return rows[0] if rows else None

    def count_for(self, device_id: UUID) -> int:
        return len([r for r in self.rows if r.device_id == device_id])


# ---------------- Phase 6 ----------------

class InMemoryLocations:
    def __init__(self) -> None:
        self.locations: set[UUID] = set()
        self.zones: list[ZoneThresholds] = []

    def add_location(self) -> UUID:
        location_id = uuid4()
        self.locations.add(location_id)
        return location_id

    def add_zone(self, location_id: UUID, name: str, low: float, high: float) -> UUID:
        zone = ZoneThresholds(uuid4(), location_id, name, low, high)
        self.zones.append(zone)
        return zone.zone_id

    def exists(self, location_id: UUID) -> bool:
        return location_id in self.locations

    def list_zones(self, location_id: UUID) -> list[ZoneThresholds]:
        return [z for z in self.zones if z.location_id == location_id]


class InMemoryRules:
    def __init__(self) -> None:
        self.rules: dict[UUID, StrategyRule] = {}
        self.writes = 0

    def get(self, location_id: UUID) -> StrategyRule | None:
        return self.rules.get(location_id)

    def upsert(self, location_id: UUID, strategy_key: str) -> StrategyRule:
        self.writes += 1
        rule = StrategyRule(location_id, strategy_key, {}, datetime.now(timezone.utc))
        self.rules[location_id] = rule
        return rule
