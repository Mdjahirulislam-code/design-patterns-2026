"""ActuatorContext: the State pattern context for one actuator.

It holds the current state object and changes it only through `apply` (a
command) or `transition_to` (a target state). Both ask the current state
first, so an illegal move raises before anything changes.
"""

from uuid import UUID

from domain.actuators.errors import IllegalTransitionError
from domain.actuators.state import INITIAL_STATE, ActuatorState, get_state


class ActuatorContext:
    def __init__(self, device_id: UUID, state: str = INITIAL_STATE) -> None:
        self.device_id = device_id
        self._state: ActuatorState = get_state(state)

    @property
    def state(self) -> str:
        return self._state.name

    def allowed_commands(self) -> list[str]:
        return self._state.allowed_commands()

    def apply(self, command: str) -> str:
        """Run a command (Phase 10 will call this). Returns the new state name."""
        self._set_state(self._state.handle(command))
        return self.state

    def transition_to(self, target: str) -> str:
        """Move to a target state if a legal command leads there."""
        target_state = get_state(target)  # unknown name -> UnknownActuatorStateError
        if target_state.name == self.state:
            raise IllegalTransitionError(
                self.state, f"go to {target_state.name}", self.allowed_commands()
            )
        return self.apply(self._state.command_to(target_state.name))

    def _set_state(self, name: str) -> None:
        self._state = get_state(name)
