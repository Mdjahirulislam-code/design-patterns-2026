"""ReadingIngest: the one ingest path. `record` is the only writer of sensor_readings."""

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from typing import Protocol
from uuid import UUID

from application.readings.dto import ReadingDto
from domain.devices.entity import Device
from domain.sensors.errors import DeviceNotFoundError, SensorReadError
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading


class DeviceLookup(Protocol):
    def get(self, device_id: UUID) -> Device | None: ...


class ReadingStore(Protocol):
    def insert(self, reading: Reading) -> Reading: ...

    def list_for_device(self, device_id: UUID, limit: int = 20) -> list[Reading]: ...


# The application only knows SensorPort. Which adapter class sits behind it is
# decided by the selector that infrastructure passes in.
SensorPortSelector = Callable[[Device], SensorPort]


def reading_to_dto(reading: Reading) -> ReadingDto:
    return ReadingDto(
        device_id=reading.device_id,
        value=reading.value,
        unit=reading.unit,
        source=reading.source,
        recorded_at=reading.recorded_at,
    )


class ReadingIngest:
    def __init__(
        self,
        devices: DeviceLookup,
        readings: ReadingStore,
        select_port: SensorPortSelector,
    ) -> None:
        self._devices = devices
        self._readings = readings
        self._select_port = select_port

    def take_reading(self, device_id: UUID, at: datetime | None = None) -> ReadingDto:
        """One-shot read: select adapter -> port.read() -> persist -> DTO.

        `at` lets the sampler stamp the row with its own clock tick.
        """
        device = self._load_sensor(device_id)
        port = self._select_port(device)
        reading = port.read(device)
        if at is not None:
            reading = replace(reading, recorded_at=at)
        return self._persist(reading)

    def record(self, device_id: UUID, reading: Reading) -> ReadingDto:
        """Persist an already translated reading (MQTT adapter output in Phase 12)."""
        self._load_sensor(device_id)
        if reading.device_id != device_id:
            raise SensorReadError("Reading belongs to a different device")
        return self._persist(reading)

    def list_readings(self, device_id: UUID, limit: int = 20) -> list[ReadingDto]:
        self._load_sensor(device_id)
        return [reading_to_dto(r) for r in self._readings.list_for_device(device_id, limit)]

    # Phase 11 will publish `reading.created` from here when tracking is on.
    def _persist(self, reading: Reading) -> ReadingDto:
        return reading_to_dto(self._readings.insert(reading))

    def _load_sensor(self, device_id: UUID) -> Device:
        device = self._devices.get(device_id)
        if device is None:
            raise DeviceNotFoundError(f"Device {device_id} not found")
        if device.role != "sensor":
            raise SensorReadError(f"Device '{device.display_name}' is not a sensor")
        return device
