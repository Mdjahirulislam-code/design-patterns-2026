"""Decorator unit tests: logging and max run time around a spy port. No database."""

import inspect
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from domain.actuators.errors import ActuatorPolicyError, MaxRunTimeExceededError
from domain.actuators.ports import ActuatorPort, ActuatorPortDecorator
from fakes import InMemoryActuatorStates, InMemoryExecutionLog, SpyActuatorPort
from infrastructure.adapters.actuators.factory import build_actuator_port
from infrastructure.adapters.actuators.logging_decorator import LoggingActuatorDecorator
from infrastructure.adapters.actuators.max_runtime_decorator import MaxRunTimeActuatorDecorator
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter

NOW = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)


def clock():
    return NOW


def states_with(device_id, state, minutes_ago):
    states = InMemoryActuatorStates()
    states.set(device_id, state, NOW - timedelta(minutes=minutes_ago))
    return states


def stack(states, inner=None):
    """logging -> max run time -> spy, with a fixed clock."""
    log = InMemoryExecutionLog()
    spy = inner or SpyActuatorPort()
    port = build_actuator_port(executions=log, states=states, clock=clock, adapter=spy)
    return port, log, spy


# ---------------- max run time ----------------

def test_max_runtime_does_not_call_inner():
    pump = uuid4()
    spy = SpyActuatorPort()
    guard = MaxRunTimeActuatorDecorator(spy, states_with(pump, "running", 31), clock=clock)

    with pytest.raises(MaxRunTimeExceededError, match="Max run time exceeded"):
        guard.apply(pump, "start", {})

    assert spy.calls == []


def test_max_runtime_blocks_at_exactly_30_minutes():
    pump = uuid4()
    spy = SpyActuatorPort()
    guard = MaxRunTimeActuatorDecorator(spy, states_with(pump, "running", 30), clock=clock)

    with pytest.raises(MaxRunTimeExceededError):
        guard.apply(pump, "stop", {})
    assert spy.calls == []


def test_max_runtime_allows_running_for_less_than_30_minutes():
    pump = uuid4()
    spy = SpyActuatorPort()
    guard = MaxRunTimeActuatorDecorator(spy, states_with(pump, "running", 29), clock=clock)

    guard.apply(pump, "start", {"duration_seconds": 30})

    assert spy.calls == [(pump, "start", {"duration_seconds": 30})]


@pytest.mark.parametrize("state", ["off", "idle", "error", "maintenance"])
def test_max_runtime_only_applies_to_running(state):
    pump = uuid4()
    spy = SpyActuatorPort()
    guard = MaxRunTimeActuatorDecorator(spy, states_with(pump, state, 600), clock=clock)

    guard.apply(pump, "start", {})

    assert len(spy.calls) == 1


def test_max_runtime_allows_actuator_without_state_row():
    pump = uuid4()
    spy = SpyActuatorPort()
    guard = MaxRunTimeActuatorDecorator(spy, InMemoryActuatorStates(), clock=clock)

    guard.apply(pump, "start", {})

    assert len(spy.calls) == 1


def test_max_runtime_limit_can_be_changed():
    pump = uuid4()
    spy = SpyActuatorPort()
    guard = MaxRunTimeActuatorDecorator(
        spy, states_with(pump, "running", 6), clock=clock, max_run_time=timedelta(minutes=5)
    )

    with pytest.raises(MaxRunTimeExceededError):
        guard.apply(pump, "start", {})


# ---------------- logging ----------------

def test_success_writes_one_logging_row():
    pump = uuid4()
    port, log, spy = stack(states_with(pump, "idle", 0))

    port.apply(pump, "start", {"duration_seconds": 30})

    assert spy.calls == [(pump, "start", {"duration_seconds": 30})]
    assert len(log.rows) == 1
    row = log.rows[0]
    assert (row.device_id, row.success, row.policy_applied, row.message) == (
        pump, True, ["logging"], None)


def test_failed_policy_writes_execution_row():
    pump = uuid4()
    port, log, spy = stack(states_with(pump, "running", 45))

    with pytest.raises(ActuatorPolicyError):
        port.apply(pump, "start", {})

    assert spy.calls == []  # the adapter was never reached
    assert len(log.rows) == 1
    row = log.rows[0]
    assert row.device_id == pump
    assert row.success is False
    assert row.policy_applied == ["maxRunTime", "logging"]
    assert row.message == "Max run time exceeded"


def test_unknown_command_still_succeeds():
    # the command string is not validated in this phase
    pump = uuid4()
    port, log, spy = stack(states_with(pump, "idle", 0))

    port.apply(pump, "fly_to_the_moon", {})

    assert spy.calls[0][1] == "fly_to_the_moon"
    assert (log.rows[0].success, log.rows[0].policy_applied, log.rows[0].message) == (
        True, ["logging"], None)


def test_adapter_failure_is_logged_and_raised_again():
    pump = uuid4()
    port, log, _ = stack(
        states_with(pump, "idle", 0), inner=SpyActuatorPort(error=ValueError("valve stuck"))
    )

    with pytest.raises(ValueError, match="valve stuck"):
        port.apply(pump, "start", {})

    row = log.rows[0]
    assert (row.success, row.policy_applied, row.message) == (False, ["logging"], "valve stuck")


def test_logging_writes_one_row_per_call():
    pump = uuid4()
    port, log, spy = stack(states_with(pump, "idle", 0))

    for command in ("start", "stop", "start"):
        port.apply(pump, command, {})

    assert len(log.rows) == 3
    assert len(spy.calls) == 3


# ---------------- the stack ----------------

def test_decorators_share_the_port_interface():
    port, _, _ = stack(InMemoryActuatorStates())

    assert isinstance(port, ActuatorPort)
    assert isinstance(port.inner, ActuatorPort)

    expected = list(inspect.signature(ActuatorPort.apply).parameters)
    for cls in (ActuatorPortDecorator, LoggingActuatorDecorator, MaxRunTimeActuatorDecorator,
                SimulationActuatorAdapter):
        assert issubclass(cls, ActuatorPort)
        assert list(inspect.signature(cls.apply).parameters) == expected


def test_chain_order_is_logging_then_max_runtime_then_adapter():
    port = build_actuator_port(executions=InMemoryExecutionLog(), states=InMemoryActuatorStates())

    assert isinstance(port, LoggingActuatorDecorator)
    assert isinstance(port.inner, MaxRunTimeActuatorDecorator)
    assert isinstance(port.inner.inner, SimulationActuatorAdapter)


def test_wrong_order_would_lose_the_blocked_attempt():
    # max run time OUTSIDE logging: the block happens before logging is reached,
    # so nothing is recorded. This is why logging must be the outermost wrapper.
    pump = uuid4()
    log = InMemoryExecutionLog()
    spy = SpyActuatorPort()
    wrong = MaxRunTimeActuatorDecorator(
        LoggingActuatorDecorator(spy, log), states_with(pump, "running", 45), clock=clock
    )

    with pytest.raises(MaxRunTimeExceededError):
        wrong.apply(pump, "start", {})

    assert log.rows == []


def test_real_chain_reaches_the_simulation_adapter():
    pump = uuid4()
    adapter = SimulationActuatorAdapter()
    log = InMemoryExecutionLog()
    port = build_actuator_port(
        executions=log, states=states_with(pump, "idle", 0), clock=clock, adapter=adapter
    )

    port.apply(pump, "start", {"duration_seconds": 10})

    assert adapter.last_for(pump).command == "start"
    assert log.rows[0].success is True
