"""Read model returned by GET /api/locations/{location_id}/overview."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OverviewLocationDto(BaseModel):
    id: UUID
    name: str = Field(examples=["Lab Site A"])


class DeviceCountsDto(BaseModel):
    """Assigned devices only (location_id and zone_id set)."""

    sensor: int = Field(examples=[1])
    actuator: int = Field(examples=[0])


class OverviewDeviceDto(BaseModel):
    id: UUID
    device_type: str = Field(examples=["moisture_sensor"])
    role: str = Field(examples=["sensor"])
    display_name: str = Field(examples=["Soil moisture sensor"])
    # Phase 8: actuators only; null / empty for sensors
    state: str | None = Field(None, examples=["idle"])
    allowed_commands: list[str] = Field(default_factory=list)


class OverviewReadingDto(BaseModel):
    """Newest sensor_readings row of one device in the zone.

    `tracking_enabled` and `sampling_interval_seconds` are copied from the device.
    """

    device_id: UUID
    value: float = Field(examples=[0.31])
    unit: str = Field(examples=["vwc"])
    recorded_at: datetime
    tracking_enabled: bool
    sampling_interval_seconds: int = Field(examples=[300])


class OverviewZoneDto(BaseModel):
    id: UUID
    name: str = Field(examples=["Zone 1"])
    moisture_threshold_low: float = Field(examples=[0.2])
    moisture_threshold_high: float = Field(examples=[0.45])
    devices: list[OverviewDeviceDto] = Field(default_factory=list)
    latest_readings: list[OverviewReadingDto] = Field(
        default_factory=list,
        description="One row per device in this zone that has a reading",
    )


class LastRecommendationDto(BaseModel):
    action: str = Field(examples=["wait"], description="irrigate or wait")
    reason: str = Field(examples=["Moisture 0.40 is within 0.25–0.45"])


class LocationOverviewDto(BaseModel):
    location: OverviewLocationDto
    device_counts: DeviceCountsDto
    zones: list[OverviewZoneDto] = Field(description="Every zone, including empty ones")
    strategy_key: str | None = Field(
        None, examples=["conservative"], description="null when no strategy is saved"
    )
    last_recommendation: LastRecommendationDto | None = Field(
        None, description="Computed by evaluate on this request; null when no strategy is saved"
    )
