"""CommandService: the one path every actuator command takes.

    1. device must be an actuator                       (else not found, no row)
    2. command_for(type) builds the command object      (unknown type: no row)
    3. guard: type must be in allowed_commands() of the saved state
           not allowed -> log "rejected", stop. No apply, no state write.
    4. invoker.run(command, port)  -> Phase 9 stack (logging -> max run time -> adapter)
           raises -> log "failed", state unchanged
    5. transition and save the state only when target_state differs
    6. log "success"
"""

from typing import Protocol
from uuid import UUID

from application.actuators.lookup import DeviceLookup, require_actuator
from application.commands.dto import CommandLogDto
from domain.actuators.context import ActuatorContext
from domain.actuators.ports import ActuatorPort
from domain.actuators.record import ActuatorStateRecord
from domain.actuators.state import INITIAL_STATE
from domain.commands.base import STATUS_FAILED, STATUS_REJECTED, STATUS_SUCCESS
from domain.commands.invoker import CommandInvoker, command_for
from domain.commands.record import CommandLogEntry


class ActuatorStateStore(Protocol):
    def get(self, device_id: UUID) -> ActuatorStateRecord | None: ...

    def save(self, device_id: UUID, state: str) -> ActuatorStateRecord: ...


class CommandLogStore(Protocol):
    def insert(
        self,
        command_type: str,
        device_id: UUID,
        payload: dict,
        status: str,
        error_message: str | None,
    ) -> CommandLogEntry: ...

    def list_recent(self, limit: int = 50) -> list[CommandLogEntry]: ...


def entry_to_dto(entry: CommandLogEntry) -> CommandLogDto:
    return CommandLogDto(
        id=entry.id,
        command_type=entry.command_type,
        device_id=entry.device_id,
        payload=dict(entry.payload),
        status=entry.status,
        error_message=entry.error_message,
        created_at=entry.created_at,
    )


class CommandService:
    def __init__(
        self,
        devices: DeviceLookup,
        states: ActuatorStateStore,
        port: ActuatorPort,
        log: CommandLogStore,
        invoker: CommandInvoker | None = None,
    ) -> None:
        self._devices = devices
        self._states = states
        self._port = port
        self._log = log
        self._invoker = invoker or CommandInvoker()

    def execute(self, command_type: str, device_id: UUID, payload: dict | None = None) -> CommandLogDto:
        require_actuator(self._devices, device_id)                 # 1
        command = command_for(command_type, device_id, payload)    # 2

        record = self._states.get(device_id)
        context = ActuatorContext(device_id, record.state if record else INITIAL_STATE)

        # 3. guard (State pattern decides, nothing is touched on reject)
        allowed = context.allowed_commands()
        if command.command_type not in allowed:
            reason = (
                f"Cannot {command.command_type} while the actuator is {context.state}. "
                f"Allowed commands: {', '.join(allowed) if allowed else 'none'}."
            )
            return self._write(command, STATUS_REJECTED, reason)

        # 4. decorated port; a policy block or adapter error is "failed"
        try:
            self._invoker.run(command, self._port)
        except Exception as error:  # noqa: BLE001 - every failure must be logged
            return self._write(command, STATUS_FAILED, str(error) or error.__class__.__name__)

        # 5. state change only when the command leads to another state
        if command.target_state is not None and command.target_state != context.state:
            context.transition(command.target_state)
            self._states.save(device_id, context.state)

        return self._write(command, STATUS_SUCCESS, None)          # 6

    def list_recent(self, limit: int = 50) -> list[CommandLogDto]:
        return [entry_to_dto(entry) for entry in self._log.list_recent(limit)]

    def _write(self, command, status: str, error_message: str | None) -> CommandLogDto:
        return entry_to_dto(
            self._log.insert(
                command.command_type, command.device_id, command.payload, status, error_message
            )
        )
