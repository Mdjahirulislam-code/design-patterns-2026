"""ActuatorExecutionService: send a command through the actuator port and read the log.

The service only knows `ActuatorPort`. It does not know that the port it gets
is a logging decorator around a max-run-time decorator around the simulation
adapter; that chain is built in infrastructure/adapters/actuators/factory.py.
"""

from typing import Protocol
from uuid import UUID

from application.actuators.dto import ExecutionDto
from application.actuators.lookup import DeviceLookup, require_actuator
from domain.actuators.execution import ActuatorExecution
from domain.actuators.ports import ActuatorPort


class ExecutionLogReader(Protocol):
    def list_recent(self, limit: int = 20) -> list[ActuatorExecution]: ...

    def latest_for_device(self, device_id: UUID) -> ActuatorExecution | None: ...


def execution_to_dto(execution: ActuatorExecution) -> ExecutionDto:
    return ExecutionDto(
        id=execution.id,
        device_id=execution.device_id,
        success=execution.success,
        policy_applied=list(execution.policy_applied),
        message=execution.message,
        created_at=execution.created_at,
    )


class ActuatorExecutionService:
    def __init__(
        self,
        devices: DeviceLookup,
        port: ActuatorPort,
        executions: ExecutionLogReader,
    ) -> None:
        self._devices = devices
        self._port = port
        self._executions = executions

    def apply(self, device_id: UUID, command: str, payload: dict | None = None) -> ExecutionDto:
        """Apply a command and return the execution row that was written for it.

        The command is not validated here (Phase 10 does that). A blocked or
        failed attempt raises; its row is already in the log by then.
        """
        require_actuator(self._devices, device_id)

        self._port.apply(device_id, command, dict(payload or {}))

        written = self._executions.latest_for_device(device_id)
        if written is None:
            raise RuntimeError("The actuator port did not write an execution row")
        return execution_to_dto(written)

    def list_recent(self, limit: int = 20) -> list[ExecutionDto]:
        return [execution_to_dto(row) for row in self._executions.list_recent(limit)]
