"""ActuatorStateService and DeviceQueryService with in-memory repositories."""

from uuid import uuid4

import pytest

from application.actuators.service import ActuatorStateService
from application.devices.queries import DeviceQueryService
from domain.actuators.errors import (
    ActuatorNotFoundError,
    IllegalTransitionError,
    UnknownActuatorStateError,
)
from fakes import InMemoryActuatorStates, InMemoryDevices, make_actuator, make_sensor


def build():
    devices = InMemoryDevices()
    states = InMemoryActuatorStates()
    pump = devices.place(make_actuator("water_pump"))
    light = devices.place(make_actuator("grow_light"))
    sensor = devices.place(make_sensor("moisture_sensor"))
    states.set(pump.id, "idle")
    states.set(light.id, "idle")
    return ActuatorStateService(devices, states), devices, states, pump, light, sensor


def test_legal_transition_is_saved():
    service, _, states, pump, _, _ = build()

    result = service.transition(pump.id, "running")

    assert (result.state, result.allowed_commands) == ("running", ["stop", "report_fault"])
    assert states.get(pump.id).state == "running"
    assert states.writes == 1


def test_illegal_transition_raises_and_is_not_saved():
    service, _, states, pump, _, _ = build()
    service.transition(pump.id, "running")
    before = states.get(pump.id)

    with pytest.raises(IllegalTransitionError):
        service.transition(pump.id, "maintenance")

    assert states.get(pump.id) == before  # same state, same updated_at
    assert states.writes == 1


def test_unknown_target_is_rejected_and_not_saved():
    service, _, states, pump, _, _ = build()

    with pytest.raises(UnknownActuatorStateError):
        service.transition(pump.id, "flying")
    assert states.writes == 0


def test_missing_device_and_sensor_are_not_actuators():
    service, _, states, _, _, sensor = build()

    with pytest.raises(ActuatorNotFoundError, match="not found"):
        service.transition(uuid4(), "running")
    with pytest.raises(ActuatorNotFoundError, match="not an actuator"):
        service.transition(sensor.id, "running")
    with pytest.raises(ActuatorNotFoundError):
        service.get(sensor.id)
    assert states.writes == 0


def test_actuator_without_row_starts_idle_and_gets_a_row_on_first_move():
    service, devices, states, _, _, _ = build()
    fan = devices.place(make_actuator("vent_fan"))

    assert service.get(fan.id).state == "idle"
    assert service.get(fan.id).updated_at is None

    service.transition(fan.id, "running")
    assert states.get(fan.id).state == "running"


def test_each_actuator_has_its_own_state():
    service, _, states, pump, light, _ = build()

    service.transition(pump.id, "running")

    assert states.get(pump.id).state == "running"
    assert states.get(light.id).state == "idle"


def test_device_list_includes_state_for_actuators_only():
    _, devices, states, pump, light, sensor = build()
    states.set(pump.id, "maintenance")
    queries = DeviceQueryService(devices, states)

    by_id = {d.id: d for d in queries.list_devices()}

    assert (by_id[pump.id].state, by_id[pump.id].allowed_commands) == (
        "maintenance", ["end_maintenance", "report_fault"])
    assert by_id[light.id].state == "idle"
    assert (by_id[sensor.id].state, by_id[sensor.id].allowed_commands) == (None, [])
    assert states.bulk_calls == 1  # one query for all actuators


def test_device_list_filters_by_role():
    _, devices, states, pump, light, _ = build()

    actuators = DeviceQueryService(devices, states).list_devices(role="actuator")

    assert {d.id for d in actuators} == {pump.id, light.id}
