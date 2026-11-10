"""State pattern: one class per actuator lifecycle state.

Each state object owns its legal commands and the state each command leads to.
The context (ActuatorContext) delegates to the current state object and swaps
it after a legal command. There is no if/elif on state names anywhere else.

Legal transitions (command -> new state):

| from        | command           | to          |
|-------------|-------------------|-------------|
| off         | power_on          | idle        |
| idle        | start             | running     |
| idle        | power_off         | off         |
| idle        | begin_maintenance | maintenance |
| idle        | report_fault      | error       |
| running     | stop              | idle        |
| running     | report_fault      | error       |
| error       | reset             | idle        |
| error       | begin_maintenance | maintenance |
| error       | power_off         | off         |
| maintenance | end_maintenance   | idle        |
| maintenance | report_fault      | error       |

Everything else is illegal, for example running -> maintenance (stop first),
off -> running (power on first) and off -> error (an unpowered device cannot fault).
"""

from abc import ABC
from types import MappingProxyType

from domain.actuators.errors import IllegalTransitionError, UnknownActuatorStateError

OFF = "off"
IDLE = "idle"
RUNNING = "running"
ERROR = "error"
MAINTENANCE = "maintenance"

# A new actuator, and one without a stored row, starts here.
INITIAL_STATE = IDLE


class ActuatorState(ABC):
    """One lifecycle state. Subclasses only declare their name and transitions."""

    name: str
    description: str
    # command -> name of the next state
    transitions: MappingProxyType

    def allowed_commands(self) -> list[str]:
        return list(self.transitions)

    def allowed_targets(self) -> list[str]:
        return list(dict.fromkeys(self.transitions.values()))

    def handle(self, command: str) -> str:
        """Return the next state for a legal command, or raise."""
        target = self.transitions.get(command)
        if target is None:
            raise IllegalTransitionError(self.name, command, self.allowed_commands())
        return target

    def command_to(self, target: str) -> str:
        """The command that leads to `target`, or raise if there is none."""
        for command, next_state in self.transitions.items():
            if next_state == target:
                return command
        raise IllegalTransitionError(
            self.name, f"go to {target}", self.allowed_commands()
        )


class OffState(ActuatorState):
    name = OFF
    description = "Powered off. Must be powered on before it can run."
    transitions = MappingProxyType({"power_on": IDLE})


class IdleState(ActuatorState):
    name = IDLE
    description = "Powered and ready, not running."
    transitions = MappingProxyType({
        "start": RUNNING,
        "power_off": OFF,
        "begin_maintenance": MAINTENANCE,
        "report_fault": ERROR,
    })


class RunningState(ActuatorState):
    name = RUNNING
    description = "Running (pump watering or light on). Must stop before maintenance."
    transitions = MappingProxyType({
        "stop": IDLE,
        "report_fault": ERROR,
    })


class ErrorState(ActuatorState):
    name = ERROR
    description = "A fault was reported. Reset, repair or power off."
    transitions = MappingProxyType({
        "reset": IDLE,
        "begin_maintenance": MAINTENANCE,
        "power_off": OFF,
    })


class MaintenanceState(ActuatorState):
    name = MAINTENANCE
    description = "Being serviced. Cannot run until maintenance ends."
    transitions = MappingProxyType({
        "end_maintenance": IDLE,
        "report_fault": ERROR,
    })


_STATES: dict[str, ActuatorState] = {
    state.name: state
    for state in (OffState(), IdleState(), RunningState(), ErrorState(), MaintenanceState())
}

STATE_NAMES: tuple[str, ...] = tuple(_STATES)


def get_state(name: str) -> ActuatorState:
    state = _STATES.get((name or "").strip().lower())
    if state is None:
        allowed = ", ".join(STATE_NAMES)
        raise UnknownActuatorStateError(f"Unknown actuator state '{name}'. Expected one of: {allowed}.")
    return state


def allowed_commands_for(name: str) -> list[str]:
    return get_state(name).allowed_commands()
