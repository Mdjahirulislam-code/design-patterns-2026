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
