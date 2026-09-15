"""Plain domain entity used by the sensor creation flow."""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(slots=True)
class Sensor:
    device_type: str
    display_name: str
    default_config: dict[str, object] = field(default_factory=dict)
    id: UUID | None = None
