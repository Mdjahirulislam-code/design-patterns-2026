from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.db import get_session
from infrastructure.persistence.device_repository import DeviceRepository

from application.actuators.dto import ActuatorStateDto, TransitionRequest
from application.actuators.service import ActuatorStateService
from application.devices.dto import DeviceDto
from application.devices.family_service import DeviceFamilyService
from application.devices.queries import DeviceQueryService

from application.locations.zone_assignment_service import ZoneAssignmentService
from application.locations.dto import ZoneAssignmentRequest

from application.readings.dto import SamplingDto, SamplingUpdateRequest
from application.readings.sampling import SamplingService
from domain.actuators.errors import (
    ActuatorNotFoundError,
    IllegalTransitionError,
    UnknownActuatorStateError,
)
from domain.sensors.errors import DeviceNotFoundError, InvalidSamplingError
from interfaces.api.dependencies import (
    get_actuator_state_service,
    get_device_queries,
    get_sampling_service,
)


router = APIRouter(
    prefix="/api/devices",
    tags=["devices"]
)


# List devices (Phase 8: actuators include state + allowed_commands)
@router.get("", response_model=list[DeviceDto], summary="List devices")
def list_devices(
    family: str | None = None,
    role: str | None = None,
    queries: DeviceQueryService = Depends(get_device_queries)
) -> list[DeviceDto]:
    return queries.list_devices(family, role)


# Create device family kit
@router.post("/provision", status_code=201, response_model=list[DeviceDto])
def provision(
    family: str,
    session: Session = Depends(get_session),
    queries: DeviceQueryService = Depends(get_device_queries)
) -> list[DeviceDto]:
    try:
        devices = DeviceFamilyService(
            DeviceRepository(session)
        ).provision_family(
            family
        )

        return queries.to_dtos(devices)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# Assign device to zone
@router.patch("/{device_id}/zone")
def assign_device_zone(
    device_id: UUID,
    request: ZoneAssignmentRequest,
    session: Session = Depends(get_session)
):
    try:
        service = ZoneAssignmentService(session)

        service.assign(
            device_id,
            request.zone_id
        )

        return {
            "message": "Device zone updated"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


# Phase 5: sampling interval + tracking flag
@router.patch(
    "/{device_id}/sampling",
    response_model=SamplingDto,
    summary="Update sampling interval and tracking",
    responses={
        400: {"description": "sampling_interval_seconds is below 5"},
        404: {"description": "Device not found"},
    },
)
def update_device_sampling(
    device_id: UUID,
    request: SamplingUpdateRequest,
    service: SamplingService = Depends(get_sampling_service)
) -> SamplingDto:
    try:
        return service.update(
            device_id,
            request.sampling_interval_seconds,
            request.tracking_enabled
        )

    except DeviceNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except InvalidSamplingError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# --------------------------------------------------
# Phase 8 — State: actuator lifecycle
# --------------------------------------------------

@router.get(
    "/{device_id}/state",
    response_model=ActuatorStateDto,
    summary="Current lifecycle state of an actuator",
    responses={404: {"description": "Actuator not found"}},
)
def get_actuator_state(
    device_id: UUID,
    service: ActuatorStateService = Depends(get_actuator_state_service)
) -> ActuatorStateDto:
    try:
        return service.get(device_id)

    except ActuatorNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.post(
    "/{device_id}/transition",
    response_model=ActuatorStateDto,
    summary="Move an actuator to another state (demo; Phase 10 uses Command)",
    responses={
        400: {"description": "Unknown target state"},
        404: {"description": "Actuator not found"},
        409: {"description": "Transition not allowed from the current state"},
    },
)
def transition_actuator(
    device_id: UUID,
    request: TransitionRequest,
    service: ActuatorStateService = Depends(get_actuator_state_service)
) -> ActuatorStateDto:
    # The router only maps errors. The rules live in domain/actuators/state.py.
    try:
        return service.transition(device_id, request.target)

    except ActuatorNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except UnknownActuatorStateError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except IllegalTransitionError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e)
        )
