"""State pattern unit tests: transition table, commands and guards. No database."""

from uuid import uuid4

import pytest

from domain.actuators.context import ActuatorContext
from domain.actuators.errors import IllegalTransitionError, UnknownActuatorStateError
from domain.actuators.state import (
    INITIAL_STATE,
    STATE_NAMES,
    ActuatorState,
    allowed_commands_for,
    get_state,
)

LEGAL = [
    ("off", "power_on", "idle"),
    ("idle", "start", "running"),
    ("idle", "power_off", "off"),
    ("idle", "begin_maintenance", "maintenance"),
    ("idle", "report_fault", "error"),
    ("running", "stop", "idle"),
    ("running", "report_fault", "error"),
    ("error", "reset", "idle"),
    ("error", "begin_maintenance", "maintenance"),
    ("error", "power_off", "off"),
    ("maintenance", "end_maintenance", "idle"),
    ("maintenance", "report_fault", "error"),
]

LEGAL_TARGETS = {(start, end) for start, _, end in LEGAL}


def ctx(state):
    return ActuatorContext(uuid4(), state)


def test_idle_to_running_allowed():
    context = ctx("idle")

    assert context.transition_to("running") == "running"
    assert context.state == "running"
    assert context.allowed_commands() == ["stop", "report_fault"]


def test_running_to_maintenance_rejected():
    context = ctx("running")

    with pytest.raises(IllegalTransitionError, match="Cannot go to maintenance while the actuator is running"):
        context.transition_to("maintenance")
    assert context.state == "running"  # unchanged


@pytest.mark.parametrize("start,command,end", LEGAL)
def test_every_legal_command(start, command, end):
    context = ctx(start)
    assert context.apply(command) == end
    assert context.state == end


@pytest.mark.parametrize("start,command,end", LEGAL)
def test_every_legal_target(start, command, end):
    assert ctx(start).transition_to(end) == end


def test_every_other_edge_is_illegal_and_leaves_state_unchanged():
    checked = 0
    for start in STATE_NAMES:
        for target in STATE_NAMES:
            if (start, target) in LEGAL_TARGETS:
                continue
            context = ctx(start)
            with pytest.raises(IllegalTransitionError):
                context.transition_to(target)
            assert context.state == start
            checked += 1
    assert checked == 25 - len(LEGAL_TARGETS)


def test_unknown_command_is_illegal():
    context = ctx("idle")
    with pytest.raises(IllegalTransitionError) as error:
        context.apply("fly")
    assert error.value.current == "idle"
    assert error.value.allowed_commands == ["start", "power_off", "begin_maintenance", "report_fault"]
    assert context.state == "idle"


def test_off_cannot_run_or_fault():
    for target in ("running", "error", "maintenance"):
        with pytest.raises(IllegalTransitionError):
            ctx("off").transition_to(target)


def test_same_state_is_not_a_transition():
    with pytest.raises(IllegalTransitionError):
        ctx("idle").transition_to("idle")


def test_unknown_state_names_are_rejected():
    with pytest.raises(UnknownActuatorStateError):
        get_state("flying")
    with pytest.raises(UnknownActuatorStateError):
        ctx("idle").transition_to("flying")
    with pytest.raises(UnknownActuatorStateError):
        ActuatorContext(uuid4(), "broken")


def test_allowed_commands_per_state():
    assert allowed_commands_for("off") == ["power_on"]
    assert allowed_commands_for("idle") == ["start", "power_off", "begin_maintenance", "report_fault"]
    assert allowed_commands_for("running") == ["stop", "report_fault"]
    assert allowed_commands_for("error") == ["reset", "begin_maintenance", "power_off"]
    assert allowed_commands_for("maintenance") == ["end_maintenance", "report_fault"]


def test_fault_and_reset_cycle():
    context = ctx("running")
    context.apply("report_fault")
    assert context.state == "error"
    context.apply("reset")
    assert context.state == "idle"


def test_each_state_is_its_own_object():
    states = [get_state(name) for name in STATE_NAMES]

    assert STATE_NAMES == ("off", "idle", "running", "error", "maintenance")
    assert all(isinstance(s, ActuatorState) for s in states)
    assert len({type(s) for s in states}) == 5
    assert INITIAL_STATE == "idle"
    assert ActuatorContext(uuid4()).state == "idle"
