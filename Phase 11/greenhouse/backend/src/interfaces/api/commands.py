"""Phase 10 — Command: execute actuator commands and list the command history.

The handler builds nothing itself and never touches an actuator adapter. It
hands the request to CommandService, which creates the command object, checks
the state, runs it through the invoker and writes command_log.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from application.commands.dto import CommandLogDto, CommandRequest
from application.commands.service import CommandService
from domain.actuators.errors import ActuatorNotFoundError
from domain.commands.base import (
    STATUS_REJECTED,
    InvalidCommandPayloadError,
    UnknownCommandError,
)
from interfaces.api.dependencies import get_command_service

router = APIRouter(prefix="/api/commands", tags=["commands"])


@router.post(
    "",
    response_model=CommandLogDto,
    summary="Execute an actuator command",
    responses={
        400: {"description": "Unknown command type or unusable payload (no row is written)"},
        404: {"description": "Device not found or not an actuator"},
        409: {
            "description": "Rejected: not allowed in the current state. The body is the log row.",
            "model": CommandLogDto,
        },
    },
)
def execute_command(
    request: CommandRequest,
    response: Response,
    service: CommandService = Depends(get_command_service),
) -> CommandLogDto:
    """`success` and `failed` answer 200 with the log row. `rejected` answers
    409 with the same row shape and does not change the actuator state."""
    try:
        row = service.execute(request.command_type, request.device_id, request.payload)
    except ActuatorNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (UnknownCommandError, InvalidCommandPayloadError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if row.status == STATUS_REJECTED:
        response.status_code = 409
    return row


@router.get(
    "",
    response_model=list[CommandLogDto],
    summary="Command history (newest first)",
)
def list_commands(
    limit: int = Query(50, ge=1, le=200, description="How many rows to return"),
    service: CommandService = Depends(get_command_service),
) -> list[CommandLogDto]:
    return service.list_recent(limit)
