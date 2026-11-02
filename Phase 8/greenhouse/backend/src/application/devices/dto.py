from uuid import UUID
from pydantic import BaseModel, Field
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
    # Phase 8: actuators only; sensors have state null and no commands
    state: str | None = Field(None, examples=["idle"], description="Actuator lifecycle state")
    allowed_commands: list[str] = Field(
        default_factory=list, examples=[["start", "power_off"]],
        description="Commands the current state allows",
    )
