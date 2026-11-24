"""Command objects, registry and invoker. No database."""

from uuid import uuid4

import pytest

from domain.commands.base import Command, InvalidCommandPayloadError, UnknownCommandError
from domain.commands.invoker import CommandInvoker, command_for, command_types
from domain.commands.light import SetLightLevelCommand
from domain.commands.pump import StartPumpCommand, StopPumpCommand
from fakes import SpyActuatorPort


def test_registry_maps_type_strings_to_classes():
    device = uuid4()

    assert command_types() == ["start_pump", "stop_pump", "set_light_level"]
    assert isinstance(command_for("start_pump", device), StartPumpCommand)
    assert isinstance(command_for("stop_pump", device), StopPumpCommand)
    assert isinstance(command_for("set_light_level", device), SetLightLevelCommand)
    assert all(isinstance(command_for(t, device), Command) for t in command_types())


def test_unknown_command_type_is_rejected_by_the_registry():
    with pytest.raises(UnknownCommandError, match="Unknown command type 'open_roof'"):
        command_for("open_roof", uuid4())


def test_target_states():
    device = uuid4()
    assert command_for("start_pump", device).target_state == "running"
    assert command_for("stop_pump", device).target_state == "idle"
    assert command_for("set_light_level", device).target_state == "running"


def test_invoker_runs_the_command_against_the_port():
    device = uuid4()
    port = SpyActuatorPort()

    CommandInvoker().run(command_for("start_pump", device, {"duration_seconds": 30}), port)

    assert port.calls == [(device, "start_pump", {"duration_seconds": 30})]


def test_set_light_level_defaults_to_level_1():
    device = uuid4()
    port = SpyActuatorPort()

    CommandInvoker().run(command_for("set_light_level", device), port)
    CommandInvoker().run(command_for("set_light_level", device, {"level": 0.4}), port)

    assert [call[2] for call in port.calls] == [{"level": 1}, {"level": 0.4}]


@pytest.mark.parametrize("level", ["high", -1, True, None])
def test_set_light_level_rejects_a_bad_level(level):
    with pytest.raises(InvalidCommandPayloadError):
        command_for("set_light_level", uuid4(), {"level": level})
