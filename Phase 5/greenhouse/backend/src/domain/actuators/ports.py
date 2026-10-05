"""ActuatorPort: unified apply operation. Phase 9 decorators wrap this port."""

from abc import ABC, abstractmethod
from uuid import UUID


class ActuatorPort(ABC):
    @abstractmethod
    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        """Send one command (for example "on", "off") to an actuator."""
        raise NotImplementedError
