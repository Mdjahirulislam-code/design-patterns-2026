"""Application service coordinating creator selection and persistence."""

from typing import Protocol

from domain.sensors.creators import get_creator
from domain.sensors.entity import Sensor


class SensorRepository(Protocol):
    def save_sensor(self, sensor: Sensor) -> Sensor: ...

    def list_sensors(self) -> list[Sensor]: ...


class SensorService:
    def __init__(self, repository: SensorRepository) -> None:
        self._repository = repository

    def create_sensor(self, sensor_type: str, display_name: str | None = None) -> Sensor:
        creator = get_creator(sensor_type)
        sensor = creator.create_sensor(display_name=display_name)
        return self._repository.save_sensor(sensor)

    def list_sensors(self) -> list[Sensor]:
        return self._repository.list_sensors()
