"""Domain events: plain records of something that already happened.

Every event carries the device and, when the device is assigned, its
location_id and zone_id (both None for an unassigned device; never invented).
`event_type` is the name used on the bus and in the alerts table.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ReadingCreated:
    """A reading was stored for a tracked device (manual read, sampler or MQTT)."""

    event_type: ClassVar[str] = "reading.created"

    device_id: UUID
    value: float
    unit: str
    source: str
    recorded_at: datetime
    location_id: UUID | None = None
    zone_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ThresholdCrossed:
    """A moisture reading was strictly below its zone's low threshold."""

    event_type: ClassVar[str] = "threshold.crossed"

    device_id: UUID | None
    location_id: UUID | None
    zone_id: UUID | None
    moisture: float
    threshold_low: float
    recorded_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CommandFailed:
    """A command was accepted but a policy or the adapter stopped it."""

    event_type: ClassVar[str] = "command.failed"

    device_id: UUID | None
    location_id: UUID | None
    zone_id: UUID | None
    command_type: str
    message: str


@dataclass(frozen=True, slots=True)
class ActuatorStateChanged:
    """An actuator state was saved (every successful transition)."""

    event_type: ClassVar[str] = "state.changed"

    device_id: UUID | None
    location_id: UUID | None
    zone_id: UUID | None
    previous_state: str | None
    state: str


@dataclass(frozen=True, slots=True)
class AlertCreated:
    """An alert row was stored. Phase 12 fans this out over the dashboard WebSocket."""

    event_type: ClassVar[str] = "alert.created"

    alert_id: UUID
    device_id: UUID | None
    location_id: UUID | None
    zone_id: UUID | None
    severity: str
    message: str
    alert_event_type: str
    created_at: datetime
