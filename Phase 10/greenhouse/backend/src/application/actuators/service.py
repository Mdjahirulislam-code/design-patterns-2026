"""ActuatorStateService: load the stored state, ask the domain, save only if legal."""

from typing import Protocol
from uuid import UUID

from application.actuators.dto import ActuatorStateDto
from application.actuators.lookup import DeviceLookup, require_actuator
from domain.actuators.context import ActuatorContext
from domain.actuators.record import ActuatorStateRecord
from domain.actuators.state import INITIAL_STATE
from domain.devices.entity import Device


class ActuatorStateStore(Protocol):
    def get(self, device_id: UUID) -> ActuatorStateRecord | None: ...

    def save(self, device_id: UUID, state: str) -> ActuatorStateRecord: ...


class ActuatorStateService:
    def __init__(self, devices: DeviceLookup, states: ActuatorStateStore) -> None:
        self._devices = devices
        self._states = states

    def get(self, device_id: UUID) -> ActuatorStateDto:
        self._require_actuator(device_id)
        context, record = self._load(device_id)
        return self._to_dto(context, record)

    def transition(self, device_id: UUID, target: str) -> ActuatorStateDto:
        """Legal: save and return the new state. Illegal: the domain raises
        IllegalTransitionError and nothing is saved."""
        self._require_actuator(device_id)
        context, _ = self._load(device_id)

        context.transition_to(target)  # raises before any write

        saved = self._states.save(device_id, context.state)
        return self._to_dto(context, saved)

    def _load(self, device_id: UUID) -> tuple[ActuatorContext, ActuatorStateRecord | None]:
        record = self._states.get(device_id)
        # an actuator without a stored row starts in the initial state
        state = record.state if record else INITIAL_STATE
        return ActuatorContext(device_id, state), record

    def _require_actuator(self, device_id: UUID) -> Device:
        return require_actuator(self._devices, device_id)

    @staticmethod
    def _to_dto(context: ActuatorContext, record: ActuatorStateRecord | None) -> ActuatorStateDto:
        return ActuatorStateDto(
            device_id=context.device_id,
            state=context.state,
            allowed_commands=context.allowed_commands(),
            updated_at=record.updated_at if record else None,
        )
