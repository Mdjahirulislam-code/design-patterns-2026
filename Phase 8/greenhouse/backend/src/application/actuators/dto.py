from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TransitionRequest(BaseModel):
    """Body of POST /api/devices/{id}/transition (demo; Phase 10 uses Command)."""

    target: str = Field(
        examples=["running"], description="off, idle, running, error or maintenance"
    )


class ActuatorStateDto(BaseModel):
    device_id: UUID
    state: str = Field(examples=["idle"])
    allowed_commands: list[str] = Field(examples=[["start", "power_off"]])
    updated_at: datetime | None = None
