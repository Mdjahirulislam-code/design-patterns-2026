"""ActuatorExecutionService with in-memory repositories and the real decorator chain."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from application.actuators.executions import ActuatorExecutionService
from domain.actuators.errors import ActuatorNotFoundError, MaxRunTimeExceededError
from fakes import (
    InMemoryActuatorStates,
    InMemoryDevices,
    InMemoryExecutionLog,
    SpyActuatorPort,
    make_actuator,
    make_sensor,
)
from infrastructure.adapters.actuators.factory import build_actuator_port

NOW = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)


class World:
    def __init__(self):
        self.devices = InMemoryDevices()
        self.states = InMemoryActuatorStates()
        self.log = InMemoryExecutionLog()
        self.adapter = SpyActuatorPort()
        self.pump = self.devices.place(make_actuator("water_pump"))
        self.light = self.devices.place(make_actuator("grow_light"))
        self.sensor = self.devices.place(make_sensor("moisture_sensor"))
        self.states.set(self.pump.id, "idle", NOW)
        self.states.set(self.light.id, "idle", NOW)
        port = build_actuator_port(
            executions=self.log, states=self.states, clock=lambda: NOW, adapter=self.adapter
        )
        self.service = ActuatorExecutionService(self.devices, port, self.log)

    def running_since(self, device, minutes_ago):
        self.states.set(device.id, "running", NOW - timedelta(minutes=minutes_ago))


def test_apply_returns_the_written_row():
    w = World()

    result = w.service.apply(w.pump.id, "start", {"duration_seconds": 30})

    assert result.device_id == w.pump.id
    assert (result.success, result.policy_applied, result.message) == (True, ["logging"], None)
    assert result.id == w.log.rows[0].id
    assert w.adapter.calls == [(w.pump.id, "start", {"duration_seconds": 30})]


def test_blocked_apply_raises_and_shows_up_in_the_log():
    w = World()
    w.running_since(w.pump, 31)

    with pytest.raises(MaxRunTimeExceededError):
        w.service.apply(w.pump.id, "start")

    (row,) = w.service.list_recent()
    assert row.device_id == w.pump.id
    assert row.success is False
    assert row.policy_applied == ["maxRunTime", "logging"]
    assert row.message == "Max run time exceeded"
    assert w.adapter.calls == []


def test_running_for_less_than_the_limit_is_not_blocked():
    w = World()
    w.running_since(w.pump, 10)

    assert w.service.apply(w.pump.id, "stop").success is True


def test_missing_device_and_sensor_are_rejected_without_a_row():
    w = World()

    with pytest.raises(ActuatorNotFoundError, match="not found"):
        w.service.apply(uuid4(), "start")
    with pytest.raises(ActuatorNotFoundError, match="not an actuator"):
        w.service.apply(w.sensor.id, "start")

    assert w.log.rows == []
    assert w.adapter.calls == []


def test_apply_does_not_change_the_actuator_state():
    # Phase 9 only forwards and logs. State changes stay with Phase 8 / Phase 10.
    w = World()
    before = w.states.get(w.pump.id)

    w.service.apply(w.pump.id, "start")

    assert w.states.get(w.pump.id) == before
    assert w.states.writes == 0


def test_list_recent_is_newest_first_and_limited():
    w = World()
    w.service.apply(w.pump.id, "start")
    w.service.apply(w.light.id, "start")
    w.service.apply(w.pump.id, "stop")

    recent = w.service.list_recent(limit=2)

    assert [r.device_id for r in recent] == [w.pump.id, w.light.id]
    assert len(w.service.list_recent()) == 3


def test_each_device_gets_its_own_row():
    w = World()
    w.running_since(w.pump, 45)

    with pytest.raises(MaxRunTimeExceededError):
        w.service.apply(w.pump.id, "start")
    ok = w.service.apply(w.light.id, "start")

    assert ok.device_id == w.light.id
    assert ok.success is True
    assert [r.success for r in w.service.list_recent()] == [True, False]
