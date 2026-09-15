"""Factory Method creators for the sensor variants supported in Phase 2."""

from abc import ABC, abstractmethod

from domain.sensors.entity import Sensor


class SensorCreator(ABC):
    @abstractmethod
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        """Create one sensor using defaults owned by the concrete creator."""
        raise NotImplementedError


class MoistureSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            device_type="moisture_sensor",
            display_name=display_name or "Soil moisture sensor",
            default_config={
                "unit": "vwc",
                "sampling_interval_seconds": 300,
                "low_moisture_threshold": 30,
            },
        )


class LightSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            device_type="light_sensor",
            display_name=display_name or "Greenhouse light sensor",
            default_config={
                "unit": "lux",
                "sampling_interval_seconds": 120,
                "low_light_threshold": 8000,
            },
        )


CREATORS: dict[str, type[SensorCreator]] = {
    "moisture": MoistureSensorCreator,
    "light": LightSensorCreator,
}


def get_creator(sensor_type: str) -> SensorCreator:
    """Resolve the short API type key to the matching concrete creator."""
    key = sensor_type.strip().lower()
    creator_class = CREATORS.get(key)
    if creator_class is None:
        allowed = ", ".join(sorted(CREATORS))
        raise ValueError(f"Unknown sensor type '{sensor_type}'. Expected one of: {allowed}.")
    return creator_class()
