from domain.actuators.state import IDLE, RUNNING
from domain.commands.base import Command


class StartPumpCommand(Command):
    command_type = "start_pump"
    target_state = RUNNING


class StopPumpCommand(Command):
    command_type = "stop_pump"
    target_state = IDLE
