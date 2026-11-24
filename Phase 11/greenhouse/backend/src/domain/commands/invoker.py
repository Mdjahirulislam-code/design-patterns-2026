"""Registry of command types and the invoker that runs a command.

The registry maps the type string to a class. There is no
`if command_type == "start_pump"` anywhere: a new command is one new class and
one registry entry.
"""

from uuid import UUID

from domain.actuators.ports import ActuatorPort
from domain.commands.base import Command, UnknownCommandError
from domain.commands.light import SetLightLevelCommand
from domain.commands.pump import StartPumpCommand, StopPumpCommand

_COMMANDS: dict[str, type[Command]] = {
    cls.command_type: cls
    for cls in (StartPumpCommand, StopPumpCommand, SetLightLevelCommand)
}


def command_types() -> list[str]:
    return list(_COMMANDS)


def command_for(command_type: str, device_id: UUID, payload: dict | None = None) -> Command:
    """Create the command object for a type string. Unknown type -> UnknownCommandError."""
    command_class = _COMMANDS.get((command_type or "").strip())
    if command_class is None:
        allowed = ", ".join(_COMMANDS)
        raise UnknownCommandError(
            f"Unknown command type '{command_type}'. Expected one of: {allowed}."
        )
    return command_class(device_id, payload)


class CommandInvoker:
    """Triggers a command. It does not know which concrete command it runs."""

    def run(self, command: Command, port: ActuatorPort) -> None:
        command.execute(port)
