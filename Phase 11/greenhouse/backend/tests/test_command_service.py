"""CommandService with in-memory repositories and the real Phase 9 decorator chain."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from application.commands.service import CommandService
from domain.actuators.errors import ActuatorNotFoundError
from domain.commands.base import UnknownCommandError
from fakes import (
    InMemoryActuatorStates,
    InMemoryCommandLog,
    InMemoryDevices,
    InMemoryExecutionLog,
    SpyActuatorPort,
    make_actuator,
    make_sensor,
)
from infrastructure.adapters.actuators.factory import build_actuator_port

NOW = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)


class World:
    def __init__(self, adapter=None):
        self.devices = InMemoryDevices()
        self.states = InMemoryActuatorStates()
        self.executions = InMemoryExecutionLog()
        self.commands = InMemoryCommandLog()
        self.adapter = adapter or SpyActuatorPort()
        self.pump = self.devices.place(make_actuator("water_pump"))
        self.light = self.devices.place(make_actuator("grow_light"))
        self.sensor = self.devices.place(make_sensor("moisture_sensor"))
        self.states.set(self.pump.id, "idle", NOW)
        self.states.set(self.light.id, "idle", NOW)
        self.states.writes = 0
        port = build_actuator_port(
            executions=self.executions, states=self.states, clock=lambda: NOW, adapter=self.adapter
        )
        self.service = CommandService(self.devices, self.states, port, self.commands)

    def state(self, device):
        return self.states.get(device.id).state


def test_start_pump_transitions_to_running():
    w = World()

    row = w.service.execute("start_pump", w.pump.id, {})

    assert (row.command_type, row.device_id, row.status, row.error_message) == (
        "start_pump", w.pump.id, "success", None)
    assert w.state(w.pump) == "running"
    assert w.adapter.calls == [(w.pump.id, "start_pump", {})]
    assert [r.status for r in w.commands.rows] == ["success"]
    # the Phase 9 decorator wrote its own row too
    assert [(e.success, e.policy_applied) for e in w.executions.rows] == [(True, ["logging"])]


def test_illegal_command_rejected_logged():
    w = World()
    before = w.states.get(w.pump.id)

    row = w.service.execute("stop_pump", w.pump.id)  # idle: stop is not allowed

    assert row.status == "rejected"
    assert "Cannot stop_pump while the actuator is idle" in row.error_message
    assert w.states.get(w.pump.id) == before   # state unchanged
    assert w.states.writes == 0
    assert w.adapter.calls == []                # the port was not reached
    assert w.executions.rows == []              # so no execution-log row either
    assert [r.status for r in w.commands.rows] == ["rejected"]


def test_start_then_stop_returns_to_idle():
    w = World()

    w.service.execute("start_pump", w.pump.id)
    again = w.service.execute("start_pump", w.pump.id)   # already running
    stopped = w.service.execute("stop_pump", w.pump.id)

    assert again.status == "rejected"
    assert stopped.status == "success"
    assert w.state(w.pump) == "idle"
    assert [r.status for r in w.commands.rows] == ["success", "rejected", "success"]


def test_set_light_level_turns_on_then_only_changes_level():
    w = World()

    first = w.service.execute("set_light_level", w.light.id)
    writes_after_first = w.states.writes
    second = w.service.execute("set_light_level", w.light.id, {"level": 0.5})

    assert (first.status, first.payload) == ("success", {"level": 1})
    assert (second.status, second.payload) == ("success", {"level": 0.5})
    assert w.state(w.light) == "running"
    assert writes_after_first == 1
    assert w.states.writes == 1  # already running: no second transition


def test_max_run_time_is_failed_and_leaves_state_unchanged():
    w = World()
    w.states.set(w.pump.id, "running", NOW - timedelta(minutes=31))
    before = w.states.get(w.pump.id)

    row = w.service.execute("stop_pump", w.pump.id)

    assert (row.status, row.error_message) == ("failed", "Max run time exceeded")
    assert w.states.get(w.pump.id) == before
    assert w.adapter.calls == []
    # the decorator's execution-log row is there as well
    (execution,) = w.executions.rows
    assert (execution.success, execution.policy_applied) == (False, ["maxRunTime", "logging"])


def test_adapter_error_is_failed():
    w = World(adapter=SpyActuatorPort(error=ValueError("valve stuck")))

    row = w.service.execute("start_pump", w.pump.id)

    assert (row.status, row.error_message) == ("failed", "valve stuck")
    assert w.state(w.pump) == "idle"


def test_unknown_type_writes_no_row():
    w = World()

    with pytest.raises(UnknownCommandError):
        w.service.execute("open_roof", w.pump.id)

    assert w.commands.rows == []
    assert w.adapter.calls == []


def test_missing_device_and_sensor_are_not_found_without_a_row():
    w = World()

    with pytest.raises(ActuatorNotFoundError):
        w.service.execute("start_pump", uuid4())
    with pytest.raises(ActuatorNotFoundError):
        w.service.execute("start_pump", w.sensor.id)

    assert w.commands.rows == []


def test_command_not_allowed_in_error_state_is_rejected():
    w = World()
    w.states.set(w.pump.id, "error", NOW)

    assert w.service.execute("start_pump", w.pump.id).status == "rejected"
    assert w.state(w.pump) == "error"


def test_history_is_newest_first_and_limited():
    w = World()
    w.service.execute("start_pump", w.pump.id)
    w.service.execute("set_light_level", w.light.id)
    w.service.execute("stop_pump", w.pump.id)

    recent = w.service.list_recent(limit=2)

    assert [r.command_type for r in recent] == ["stop_pump", "set_light_level"]
    assert len(w.service.list_recent()) == 3
