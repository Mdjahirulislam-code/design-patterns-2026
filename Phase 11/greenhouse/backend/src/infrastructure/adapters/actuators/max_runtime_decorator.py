"""Max-run-time decorator: blocks a command when the actuator has run too long.

It reads the lifecycle that Phase 8 already stores (actuator_states.state and
updated_at). It does not keep a second lifecycle of its own.

Blocked when: the stored state is "running" AND updated_at is at least
`max_run_time` (30 minutes) before the clock. Then the wrapped port is NOT
called and MaxRunTimeExceededError is raised. The command string is not looked
at in this phase; Phase 10 consults allowed_commands.
"""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import UUID

from domain.actuators.errors import MaxRunTimeExceededError
from domain.actuators.policies import MAX_RUN_TIME
from domain.actuators.ports import ActuatorPort, ActuatorPortDecorator
from domain.actuators.record import ActuatorStateRecord
from domain.actuators.state import RUNNING


class ActuatorStateReader(Protocol):
    def get(self, device_id: UUID) -> ActuatorStateRecord | None: ...


class MaxRunTimeActuatorDecorator(ActuatorPortDecorator):
    def __init__(
        self,
        inner: ActuatorPort,
        states: ActuatorStateReader,
        clock: Callable[[], datetime] | None = None,
        max_run_time: timedelta = MAX_RUN_TIME,
    ) -> None:
        super().__init__(inner)
        self._states = states
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._max_run_time = max_run_time

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        if self._has_run_too_long(self._states.get(device_id)):
            # short-circuit: the wrapped port is never reached
            raise MaxRunTimeExceededError()

        super().apply(device_id, command, payload)

    def _has_run_too_long(self, record: ActuatorStateRecord | None) -> bool:
        if record is None or record.state != RUNNING or record.updated_at is None:
            return False

        since = record.updated_at
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

        return self._clock() - since >= self._max_run_time
