from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReadingDto(BaseModel):
    """Normalized reading returned by the API."""

    device_id: UUID
    value: float = Field(examples=[0.31])
    unit: str = Field(examples=["vwc"])
    source: str = Field(examples=["simulation"], description="simulation, mqtt or vendor")
    recorded_at: datetime


class SamplingUpdateRequest(BaseModel):
    """Body of PATCH /api/devices/{id}/sampling."""

    sampling_interval_seconds: int = Field(
        examples=[30], description="Seconds between sampler readings. Minimum 5."
    )
    tracking_enabled: bool = Field(examples=[True])


class SamplingDto(BaseModel):
    device_id: UUID
    sampling_interval_seconds: int
    tracking_enabled: bool
