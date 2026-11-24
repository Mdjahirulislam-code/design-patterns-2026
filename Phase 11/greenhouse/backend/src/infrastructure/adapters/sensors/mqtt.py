"""MQTT sensor adapter: translates an inbound payload dict into a Reading.

There is no broker client and no socket here. Phase 12 delivers the same dict
over the device HTTP route or from an optional broker subscriber and passes
the translated reading to ReadingIngest.record.
"""

import math
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from domain.devices.entity import Device
from domain.sensors.errors import SensorReadError
from domain.sensors.reading import SOURCE_MQTT, Reading


class MqttSensorAdapter:
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def translate(self, device: Device, payload: dict[str, Any]) -> Reading:
        """`{"value": 0.41, "unit": "vwc"}` -> Reading with source "mqtt"."""
        if device.id is None:
            raise SensorReadError("Device has no id yet")
        if not isinstance(payload, dict):
            raise SensorReadError("MQTT payload must be an object")

        raw_value = payload.get("value")
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            raise SensorReadError("MQTT payload needs a numeric 'value'")
        if not math.isfinite(raw_value):
            raise SensorReadError("MQTT payload 'value' must be a finite number")

        unit = payload.get("unit") or device.default_config.get("unit")
        if not isinstance(unit, str) or not unit.strip():
            raise SensorReadError("MQTT payload needs a 'unit'")

        return Reading(
            device_id=device.id,
            value=float(raw_value),
            unit=unit.strip(),
            source=SOURCE_MQTT,
            recorded_at=self._clock(),
        )
