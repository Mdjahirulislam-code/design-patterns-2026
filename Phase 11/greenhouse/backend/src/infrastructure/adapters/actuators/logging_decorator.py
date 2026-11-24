"""Logging decorator: stores every attempt in actuator_execution_log.

It is the outermost wrapper, so it also sees attempts that an inner policy
blocked. One call to apply() writes exactly one row:

  completed       -> success=true,  policy_applied=["logging"],               message=null
  blocked policy  -> success=false, policy_applied=[<policy>, "logging"],     message=<reason>
  adapter failure -> success=false, policy_applied=["logging"],               message=<error>

After writing the row, the original error is raised again for the caller.
"""

from typing import Protocol
from uuid import UUID

from domain.actuators.errors import ActuatorPolicyError
from domain.actuators.policies import POLICY_LOGGING
from domain.actuators.ports import ActuatorPort, ActuatorPortDecorator


class ExecutionLogWriter(Protocol):
    def insert(
        self,
        device_id: UUID,
        success: bool,
        policy_applied: list[str],
        message: str | None,
    ) -> object: ...


class LoggingActuatorDecorator(ActuatorPortDecorator):
    def __init__(self, inner: ActuatorPort, log: ExecutionLogWriter) -> None:
        super().__init__(inner)
        self._log = log

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        try:
            super().apply(device_id, command, payload)

        except ActuatorPolicyError as blocked:
            self._log.insert(device_id, False, [blocked.policy, POLICY_LOGGING], str(blocked))
            raise

        except Exception as failed:
            message = str(failed) or failed.__class__.__name__
            self._log.insert(device_id, False, [POLICY_LOGGING], message)
            raise

        self._log.insert(device_id, True, [POLICY_LOGGING], None)
