"""ActuatorPort + simulation stub (Phase 9 will decorate this port)."""

from uuid import uuid4

import pytest

from domain.actuators.ports import ActuatorPort
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter


def test_simulation_actuator_records_command_in_memory():
    port: ActuatorPort = SimulationActuatorAdapter()
    pump = uuid4()

    port.apply(pump, "on", {"duration_seconds": 30})
    port.apply(pump, "off", {})

    assert [c.command for c in port.applied] == ["on", "off"]
    assert port.applied[0].payload == {"duration_seconds": 30}
    assert port.last_for(pump).command == "off"
    assert port.last_for(uuid4()) is None


def test_simulation_actuator_rejects_empty_command():
    with pytest.raises(ValueError):
        SimulationActuatorAdapter().apply(uuid4(), " ", {})
