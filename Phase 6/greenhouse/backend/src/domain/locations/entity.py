from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class Zone:
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict

@dataclass(frozen=True)
class LocationConfig:
    name: str
    zones: list[Zone]


# Phase 6: a stored zone's id and moisture band, as plain data for automation.
@dataclass(frozen=True)
class ZoneThresholds:
    zone_id: UUID
    location_id: UUID
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
