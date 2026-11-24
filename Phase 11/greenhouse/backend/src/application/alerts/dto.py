from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AlertDto(BaseModel):
    """One row of the alerts table (acknowledged_at is stored but not returned)."""

    id: UUID
    location_id: UUID | None = None
    zone_id: UUID | None = None
    device_id: UUID | None = None
    severity: str = Field(examples=["warning"], description="info, warning or critical")
    message: str = Field(examples=["Moisture below zone low"])
    event_type: str = Field(examples=["threshold.crossed"])
    status: str = Field(examples=["active"], description="active or resolved")
    created_at: datetime
