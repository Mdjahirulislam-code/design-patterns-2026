"""Shared check: the device exists and is an actuator."""

from typing import Protocol
from uuid import UUID

from domain.actuators.errors import ActuatorNotFoundError
from domain.devices.entity import Device

ACTUATOR = "actuator"


class DeviceLookup(Protocol):
    def get(self, device_id: UUID) -> Device | None: ...


def require_actuator(devices: DeviceLookup, device_id: UUID) -> Device:
    device = devices.get(device_id)
    if device is None:
        raise ActuatorNotFoundError(f"Device {device_id} not found")
    if device.role != ACTUATOR:
        raise ActuatorNotFoundError(f"Device {device_id} is not an actuator")
    return device
