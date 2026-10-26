"""SimulationSampler: records simulation sensors on their own interval.

`run_once(now)` is plain and synchronous so tests can drive it with a fake
clock. The background loop that calls it lives in main.py (app lifespan).
No broker connection here: MQTT devices are skipped, they push on their own.
"""

import logging
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from application.readings.service import ReadingIngest
from domain.devices.entity import PROTOCOL_SIMULATION, Device
from domain.sensors.errors import DeviceNotFoundError, SensorReadError
from domain.sensors.reading import Reading

logger = logging.getLogger(__name__)


class SensorDirectory(Protocol):
    def list_sensors(self) -> list[Device]: ...


class LatestReadings(Protocol):
    def latest_for_device(self, device_id: UUID) -> Reading | None: ...


class SimulationSampler:
    def __init__(
        self,
        devices: SensorDirectory,
        readings: LatestReadings,
        ingest: ReadingIngest,
    ) -> None:
        self._devices = devices
        self._readings = readings
        self._ingest = ingest

    def run_once(self, now: datetime) -> int:
        """Record every due device once. Returns how many rows were added."""
        recorded = 0

        for device in self._devices.list_sensors():
            if not self._should_sample(device):
                continue
            if not self._is_due(device, now):
                continue

            try:
                self._ingest.take_reading(device.id, at=now)
                recorded += 1
            except (SensorReadError, DeviceNotFoundError) as exc:
                # one broken device must not stop the others
                logger.warning("Sampler skipped %s: %s", device.id, exc)

        return recorded

    @staticmethod
    def _should_sample(device: Device) -> bool:
        if device.id is None or device.role != "sensor":
            return False
        if not device.tracking_enabled:
            return False
        if device.protocol != PROTOCOL_SIMULATION:
            return False  # mqtt devices send their own readings
        if device.uses_vendor_stub:
            return False  # vendor stub is read manually only ("Read now")
        return True

    def _is_due(self, device: Device, now: datetime) -> bool:
        last = self._readings.latest_for_device(device.id)
        if last is None:
            return True  # no previous row counts as elapsed
        interval = timedelta(seconds=device.sampling_interval_seconds)
        return now - last.recorded_at >= interval
