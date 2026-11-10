"""DeviceQueryService: device read models with actuator state attached.

States for all listed actuators are loaded in one query (no query per device).
"""

from typing import Protocol
from uuid import UUID

from application.devices.dto import DeviceDto
from application.devices.mappers import device_to_dto
from domain.devices.entity import Device


class DeviceListing(Protocol):
    def list_devices(self, device_family=None, role=None) -> list[Device]: ...

    def list_in_zone(self, location_id: UUID, zone_id: UUID) -> list[Device]: ...


class ActuatorStateLookup(Protocol):
    def get_many(self, device_ids: list[UUID]) -> dict[UUID, str]: ...


class DeviceQueryService:
    def __init__(self, devices: DeviceListing, states: ActuatorStateLookup) -> None:
        self._devices = devices
        self._states = states

    def list_devices(self, family: str | None = None, role: str | None = None) -> list[DeviceDto]:
        return self.to_dtos(self._devices.list_devices(device_family=family, role=role))

    def list_in_zone(self, location_id: UUID, zone_id: UUID) -> list[DeviceDto]:
        return self.to_dtos(self._devices.list_in_zone(location_id, zone_id))

    def to_dtos(self, devices: list[Device]) -> list[DeviceDto]:
        actuator_ids = [d.id for d in devices if d.role == "actuator" and d.id is not None]
        states = self._states.get_many(actuator_ids) if actuator_ids else {}
        return [device_to_dto(device, states.get(device.id)) for device in devices]
