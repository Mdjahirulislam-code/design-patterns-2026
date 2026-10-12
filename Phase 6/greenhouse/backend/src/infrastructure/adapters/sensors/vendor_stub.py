"""Vendor stub adapter.

`AcmeProbeClient` plays the vendor SDK (the adaptee). It answers in its own
shape: other field names, percent / kilolux units, epoch milliseconds and a
status code. `VendorStubSensorAdapter` translates that into `Reading`.

This is a translation exercise only. It is not the ESP32 path (that is MQTT).
"""

import random
from datetime import datetime, timezone
from typing import Any, Protocol

from domain.devices.entity import Device
from domain.sensors.errors import SensorReadError
from domain.sensors.ports import SensorPort
from domain.sensors.reading import SOURCE_VENDOR, Reading


class VendorClient(Protocol):
    def poll(self, probe_serial: str, channel: str) -> dict[str, Any]: ...


class AcmeProbeClient:
    """Fake vendor SDK. Returns the vendor's raw payload."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def poll(self, probe_serial: str, channel: str) -> dict[str, Any]:
        if channel == "SOIL_H2O":
            measurement = {"qty": "SOIL_H2O", "val": round(self._rng.uniform(20, 60), 1), "uom": "PCT"}
        elif channel == "ILLUM":
            measurement = {"qty": "ILLUM", "val": round(self._rng.uniform(0.2, 2.0), 3), "uom": "KLX"}
        else:
            return {"probeSerial": probe_serial, "statusCode": 4, "statusText": "UNKNOWN_CHANNEL"}

        return {
            "probeSerial": probe_serial,
            "statusCode": 0,
            "statusText": "OK",
            "tsEpochMs": int(datetime.now(timezone.utc).timestamp() * 1000),
            "measurement": measurement,
        }


# our device_type -> vendor channel name
_CHANNELS = {
    "moisture_sensor": "SOIL_H2O",
    "light_sensor": "ILLUM",
}

# vendor unit -> (our unit, factor to multiply the vendor value with)
_UNITS = {
    "PCT": ("vwc", 0.01),   # 41.0 %   -> 0.41 vwc
    "KLX": ("lux", 1000.0),  # 1.2 klx -> 1200 lux
}


class VendorStubSensorAdapter(SensorPort):
    def __init__(self, client: VendorClient | None = None) -> None:
        self._client = client or AcmeProbeClient()

    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise SensorReadError("Device has no id yet")

        channel = _CHANNELS.get(device.device_type)
        if channel is None:
            raise SensorReadError(
                f"Vendor adapter cannot read device type '{device.device_type}'"
            )

        raw = self._client.poll(probe_serial=str(device.id), channel=channel)
        return self.translate(device, raw)

    def translate(self, device: Device, raw: dict[str, Any]) -> Reading:
        """Vendor payload -> normalized Reading. Translation only, no policy."""
        if device.id is None:
            raise SensorReadError("Device has no id yet")

        if raw.get("statusCode") != 0:
            raise SensorReadError(
                f"Vendor probe error {raw.get('statusCode')}: {raw.get('statusText', 'unknown')}"
            )

        try:
            measurement = raw["measurement"]
            unit, factor = _UNITS[measurement["uom"]]
            value = float(measurement["val"]) * factor
            recorded_at = datetime.fromtimestamp(raw["tsEpochMs"] / 1000, tz=timezone.utc)
        except (KeyError, TypeError, ValueError) as exc:
            raise SensorReadError(f"Vendor payload could not be translated: {exc!r}") from exc

        return Reading(
            device_id=device.id,
            value=round(value, 4),
            unit=unit,
            source=SOURCE_VENDOR,
            recorded_at=recorded_at,
        )
