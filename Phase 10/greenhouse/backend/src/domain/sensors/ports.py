"""SensorPort: the target interface application code talks to.

No FastAPI, SQLAlchemy or Pydantic here, and no broker client.
"""

from abc import ABC, abstractmethod

from domain.devices.entity import Device
from domain.sensors.reading import Reading


class SensorPort(ABC):
    @abstractmethod
    def read(self, device: Device) -> Reading:
        """Take one reading from the device and return it in the normalized shape.

        Raises SensorReadError when the device cannot be read.
        """
        raise NotImplementedError
