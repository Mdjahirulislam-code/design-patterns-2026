"""Plain input and output of a strategy. No ORM, HTTP or Pydantic types."""

from dataclasses import dataclass
from uuid import UUID

ACTION_IRRIGATE = "irrigate"
ACTION_WAIT = "wait"


@dataclass(frozen=True, slots=True)
class LocationAutomationContext:
    """Everything a strategy may look at for ONE zone of a location.

    `moisture` is the latest reading among moisture sensors whose
    devices.zone_id is this zone. It is None when the zone has no moisture
    sensor or that sensor has no stored reading yet. A zone never borrows a
    reading from another zone or from an unassigned device.
    """

    location_id: UUID
    zone_id: UUID
    zone_name: str
    low: float
    high: float
    moisture: float | None = None
    has_moisture_sensor: bool = False
    light: float | None = None

    def __post_init__(self) -> None:
        if self.low >= self.high:
            raise ValueError("Zone low threshold must be lower than the high threshold")


@dataclass(frozen=True, slots=True)
class Recommendation:
    """What a strategy recommends. It does not start any pump by itself."""

    action: str  # "irrigate" | "wait"
    reason: str
    score: float | None = None  # 0..1, how strongly irrigation is needed
