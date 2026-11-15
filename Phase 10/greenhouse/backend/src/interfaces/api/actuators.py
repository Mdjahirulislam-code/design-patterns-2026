"""Phase 9 — Decorator: the actuator execution log and a demo apply route.

The handlers only call ActuatorExecutionService. No policy is checked here:
logging and max run time are decorator classes around the actuator port
(infrastructure/adapters/actuators/).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from application.actuators.dto import ApplyCommandRequest, ExecutionDto
from application.actuators.executions import ActuatorExecutionService
from domain.actuators.errors import ActuatorNotFoundError, ActuatorPolicyError
from interfaces.api.dependencies import get_execution_service

router = APIRouter(prefix="/api/actuators", tags=["actuators"])


@router.get(
    "/executions",
    response_model=list[ExecutionDto],
    summary="Recent actuator executions (newest first)",
)
def list_executions(
    limit: int = Query(20, ge=1, le=200, description="How many rows to return"),
    service: ActuatorExecutionService = Depends(get_execution_service),
) -> list[ExecutionDto]:
    """Rows of `actuator_execution_log`. Every attempt is stored, also a blocked one."""
    return service.list_recent(limit)


@router.post(
    "/{device_id}/apply",
    response_model=ExecutionDto,
    summary="Send a command through the decorated actuator port (demo; Phase 10 uses Command)",
    responses={
        400: {"description": "The adapter rejected the command (for example an empty command)"},
        404: {"description": "Actuator not found"},
        409: {"description": "Blocked by a policy, for example max run time exceeded"},
    },
)
def apply_command(
    device_id: UUID,
    request: ApplyCommandRequest,
    service: ActuatorExecutionService = Depends(get_execution_service),
) -> ExecutionDto:
    """The command is not validated in this phase. It succeeds unless the
    actuator has been `running` for 30 minutes. Blocked and failed attempts are
    still written to the execution log with `success=false`."""
    try:
        return service.apply(device_id, request.command, request.payload)
    except ActuatorNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ActuatorPolicyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
