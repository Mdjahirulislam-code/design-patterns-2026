"""Application service coordinating creator selection and persistence."""

from typing import Protocol

from domain.sensors.creators import get_creator
from domain.sensors.entity import Sensor

ADAPTER_CHOICES = ("simulation", "vendor")


class SensorRepository(Protocol):
    def save_sensor(self, sensor: Sensor) -> Sensor: ...

    def list_sensors(self) -> list[Sensor]: ...


class SensorService:
    def __init__(self, repository: SensorRepository) -> None:
        self._repository = repository

    def create_sensor(
        self,
        sensor_type: str,
        display_name: str | None = None,
        adapter: str = "simulation",
    ) -> Sensor:
        if adapter not in ADAPTER_CHOICES:
            allowed = ", ".join(ADAPTER_CHOICES)
            raise ValueError(f"Unknown adapter '{adapter}'. Expected one of: {allowed}.")

        creator = get_creator(sensor_type)
        sensor = creator.create_sensor(display_name=display_name)

        if adapter == "vendor":
            # Phase 5: this flag makes the selector pick the vendor stub adapter.
            sensor.default_config["vendor_stub"] = True
            if display_name is None:
                sensor.display_name = f"Vendor {sensor.display_name[0].lower()}{sensor.display_name[1:]}"

        return self._repository.save_sensor(sensor)

    def list_sensors(self) -> list[Sensor]:
        return self._repository.list_sensors()
