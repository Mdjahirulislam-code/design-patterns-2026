from uuid import UUID
from pydantic import BaseModel
class DeviceDto(BaseModel):
    id: UUID
    device_type: str
    role: str
    device_family: str
    display_name: str
    default_config: dict
    zone_id: UUID | None = None
    # Phase 5
    sampling_interval_seconds: int = 300
    tracking_enabled: bool = True
