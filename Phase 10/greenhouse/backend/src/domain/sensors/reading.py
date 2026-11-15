"""Normalized reading: the one shape every sensor adapter must produce."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

SOURCE_SIMULATION = "simulation"
SOURCE_MQTT = "mqtt"
SOURCE_VENDOR = "vendor"

SOURCES = (SOURCE_SIMULATION, SOURCE_MQTT, SOURCE_VENDOR)


@dataclass(frozen=True, slots=True)
class Reading:
    device_id: UUID
    value: float
    unit: str
    source: str
    recorded_at: datetime

    def __post_init__(self) -> None:
        if self.source not in SOURCES:
            raise ValueError(f"Unknown reading source '{self.source}'")
        if not self.unit:
            raise ValueError("Reading unit is required")
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("Reading recorded_at must be timezone-aware")
