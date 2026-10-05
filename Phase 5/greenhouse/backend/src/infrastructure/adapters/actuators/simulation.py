"""Simulation actuator adapter: remembers and logs the command. No GPIO."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from domain.actuators.ports import ActuatorPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppliedCommand:
    device_id: UUID
    command: str
    payload: dict
    applied_at: datetime


class SimulationActuatorAdapter(ActuatorPort):
    def __init__(self) -> None:
        self.applied: list[AppliedCommand] = []

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        if not command or not command.strip():
            raise ValueError("Actuator command is required")

        entry = AppliedCommand(
            device_id=device_id,
            command=command.strip(),
            payload=dict(payload or {}),
            applied_at=datetime.now(timezone.utc),
        )
        self.applied.append(entry)
        logger.info(
            "Simulated actuator %s: %s %s", entry.device_id, entry.command, entry.payload
        )

    def last_for(self, device_id: UUID) -> AppliedCommand | None:
        for entry in reversed(self.applied):
            if entry.device_id == device_id:
                return entry
        return None
