from uuid import UUID

from pydantic import BaseModel


# Request model for creating/updating a zone
class ZoneRequest(BaseModel):
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict | None = None


# Request model for creating a location configuration
class LocationRequest(BaseModel):
    location_name: str
    zones: list[ZoneRequest]


# Request model for assigning a device to a zone
class ZoneAssignmentRequest(BaseModel):
    zone_id: UUID | None