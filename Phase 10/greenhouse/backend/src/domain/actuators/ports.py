"""ActuatorPort: unified apply operation, and the base class of its decorators.

Component:          ActuatorPort
Concrete component: SimulationActuatorAdapter (infrastructure)
Decorator:          ActuatorPortDecorator (this file)
Concrete decorators: LoggingActuatorDecorator, MaxRunTimeActuatorDecorator (infrastructure)
"""

from abc import ABC, abstractmethod
from uuid import UUID


class ActuatorPort(ABC):
    @abstractmethod
    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        """Send one command (for example "start", "stop") to an actuator."""
        raise NotImplementedError


class ActuatorPortDecorator(ActuatorPort):
    """Phase 9: wraps another ActuatorPort and has exactly the same interface.

    The default `apply` only forwards to the wrapped port. A concrete decorator
    overrides it to add one policy before or after `super().apply(...)`.
    Callers hold an ActuatorPort and never need to know how many wrappers there are.
    """

    def __init__(self, inner: ActuatorPort) -> None:
        self._inner = inner

    @property
    def inner(self) -> ActuatorPort:
        """The wrapped port (read only; used to inspect the chain in tests)."""
        return self._inner

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        self._inner.apply(device_id, command, payload)
