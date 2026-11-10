"""Update the per-device sampling settings (PATCH /api/devices/{id}/sampling)."""

from typing import Protocol
from uuid import UUID

from application.readings.dto import SamplingDto
from domain.devices.entity import MIN_SAMPLING_INTERVAL_SECONDS, Device
from domain.sensors.errors import DeviceNotFoundError, InvalidSamplingError


class SamplingStore(Protocol):
    def update_sampling(
        self, device_id: UUID, sampling_interval_seconds: int, tracking_enabled: bool
    ) -> Device | None: ...


class SamplingService:
    def __init__(self, devices: SamplingStore) -> None:
        self._devices = devices

    def update(
        self, device_id: UUID, sampling_interval_seconds: int, tracking_enabled: bool
    ) -> SamplingDto:
        if sampling_interval_seconds < MIN_SAMPLING_INTERVAL_SECONDS:
            raise InvalidSamplingError(
                f"sampling_interval_seconds must be at least {MIN_SAMPLING_INTERVAL_SECONDS}"
            )

        device = self._devices.update_sampling(
            device_id, sampling_interval_seconds, tracking_enabled
        )
        if device is None:
            raise DeviceNotFoundError(f"Device {device_id} not found")

        return SamplingDto(
            device_id=device.id,
            sampling_interval_seconds=device.sampling_interval_seconds,
            tracking_enabled=device.tracking_enabled,
        )
