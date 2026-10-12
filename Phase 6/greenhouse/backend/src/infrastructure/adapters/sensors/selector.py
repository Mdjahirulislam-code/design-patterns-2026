"""Adapter selection. The only place that names concrete sensor adapters.

Rule (documented in docs/patterns/adapter.md):

1. `default_config.vendor_stub == true`    -> VendorStubSensorAdapter
2. `default_config.protocol == simulation` -> SimulationSensorAdapter
3. `default_config.protocol == mqtt`       -> no pull adapter. The device pushes
   its payload and MqttSensorAdapter.translate turns it into a Reading.

The vendor stub has its own flag, so it never collides with the two protocols.
"""

from domain.devices.entity import PROTOCOL_MQTT, PROTOCOL_SIMULATION, Device
from domain.sensors.errors import SensorReadError
from domain.sensors.ports import SensorPort
from infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter

_simulation = SimulationSensorAdapter()
_vendor = VendorStubSensorAdapter()


def select_sensor_port(device: Device) -> SensorPort:
    if device.role != "sensor":
        raise SensorReadError(f"Device '{device.display_name}' is not a sensor")

    if device.uses_vendor_stub:
        return _vendor

    if device.protocol == PROTOCOL_SIMULATION:
        return _simulation

    if device.protocol == PROTOCOL_MQTT:
        raise SensorReadError(
            "MQTT sensors push their own readings and cannot be read on demand"
        )

    raise SensorReadError(f"No sensor adapter for protocol '{device.protocol}'")
