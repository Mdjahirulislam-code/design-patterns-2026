"""Command: one operator request to an actuator, as an object.

The command knows WHAT to send (its type, device and payload) and which state
a successful run leads to. It does not check the state, save anything or
write the log; the application service does that around `execute`.
"""

from abc import ABC
from dataclasses import dataclass
from uuid import UUID

from domain.actuators.ports import ActuatorPort

STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_REJECTED = "rejected"


class UnknownCommandError(ValueError):
    """The command type is not registered (HTTP 400, no command_log row)."""


class InvalidCommandPayloadError(ValueError):
    """The payload cannot be used by this command (HTTP 400, no command_log row)."""


@dataclass(frozen=True, slots=True)
class CommandResult:
    status: str  # success | failed | rejected
    error_message: str | None = None


class Command(ABC):
    command_type: str
    # state after a successful run; None means "no state change"
    target_state: str | None = None

    def __init__(self, device_id: UUID, payload: dict | None = None) -> None:
        self.device_id = device_id
        self.payload = self.prepare_payload(dict(payload or {}))

    def prepare_payload(self, payload: dict) -> dict:
        """Hook for a command that needs defaults or checks on its payload."""
        return payload

    def execute(self, port: ActuatorPort) -> None:
        """Send the request to the receiver (the decorated actuator port)."""
        port.apply(self.device_id, self.command_type, self.payload)
