"""Stored actuator state as plain data (no ORM row leaves the repository)."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ActuatorStateRecord:
    device_id: UUID
    state: str
    updated_at: datetime | None = None
