"""One stored row of command_log (plain data)."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CommandLogEntry:
    id: UUID
    command_type: str
    device_id: UUID
    payload: dict
    status: str
    error_message: str | None
    created_at: datetime
