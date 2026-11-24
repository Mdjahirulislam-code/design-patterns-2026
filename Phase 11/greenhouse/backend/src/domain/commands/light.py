from domain.actuators.state import RUNNING
from domain.commands.base import Command, InvalidCommandPayloadError

DEFAULT_LIGHT_LEVEL = 1


class SetLightLevelCommand(Command):
    """Turns the light on at a level. On an already running light only the level changes."""

    command_type = "set_light_level"
    target_state = RUNNING

    def prepare_payload(self, payload: dict) -> dict:
        level = payload.get("level", DEFAULT_LIGHT_LEVEL)
        if isinstance(level, bool) or not isinstance(level, (int, float)) or level < 0:
            raise InvalidCommandPayloadError("set_light_level needs a number 'level' of 0 or more")
        return {**payload, "level": level}
