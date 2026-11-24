"""Simulation adapter: generates a plausible value in code. No hardware."""

import random
from collections.abc import Callable
from datetime import datetime, timezone

from domain.devices.entity import Device
from domain.sensors.errors import SensorReadError
from domain.sensors.ports import SensorPort
from domain.sensors.reading import SOURCE_SIMULATION, Reading

# device_type -> (low, high, unit, decimals)
SIMULATION_RANGES: dict[str, tuple[float, float, str, int]] = {
    "moisture_sensor": (0.2, 0.6, "vwc", 3),
    "light_sensor": (200.0, 2000.0, "lux", 1),
}


class SimulationSensorAdapter(SensorPort):
    def __init__(
        self,
        rng: random.Random | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._rng = rng or random.Random()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise SensorReadError("Device has no id yet")

        spec = SIMULATION_RANGES.get(device.device_type)
        if spec is None:
            raise SensorReadError(
                f"Simulation adapter cannot read device type '{device.device_type}'"
            )

        low, high, unit, decimals = spec
        value = round(self._rng.uniform(low, high), decimals)
        # rounding can never leave the range, but keep the guarantee explicit
        value = min(max(value, low), high)

        return Reading(
            device_id=device.id,
            value=value,
            unit=unit,
            source=SOURCE_SIMULATION,
            recorded_at=self._clock(),
        )
