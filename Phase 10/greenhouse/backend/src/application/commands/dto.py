from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CommandRequest(BaseModel):
    """Body of POST /api/commands."""

    command_type: str = Field(examples=["start_pump"])
    device_id: UUID
    payload: dict = Field(default_factory=dict, examples=[{}])


class CommandLogDto(BaseModel):
    """One row of command_log."""

    id: UUID
    command_type: str = Field(examples=["start_pump"])
    device_id: UUID
    payload: dict
    status: str = Field(examples=["success"], description="success, failed or rejected")
    error_message: str | None = None
    created_at: datetime
