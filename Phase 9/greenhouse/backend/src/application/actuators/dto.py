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


# ---------------- Phase 9: execution log ----------------

class ApplyCommandRequest(BaseModel):
    """Body of POST /api/actuators/{device_id}/apply (demo; Phase 10 uses Command)."""

    command: str = Field(
        examples=["start"],
        description="Sent to the actuator port as it is. Not validated in this phase.",
    )
    payload: dict = Field(default_factory=dict, examples=[{}])


class ExecutionDto(BaseModel):
    """One row of actuator_execution_log."""

    id: UUID
    device_id: UUID
    success: bool = Field(examples=[False])
    policy_applied: list[str] = Field(examples=[["maxRunTime", "logging"]])
    message: str | None = Field(None, examples=["Max run time exceeded"])
    created_at: datetime
