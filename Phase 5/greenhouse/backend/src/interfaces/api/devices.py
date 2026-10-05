from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.db import get_session
from infrastructure.persistence.device_repository import DeviceRepository

from application.devices.family_service import DeviceFamilyService
from application.devices.mappers import device_to_dto

from application.locations.zone_assignment_service import ZoneAssignmentService
from application.locations.dto import ZoneAssignmentRequest

from application.readings.dto import SamplingDto, SamplingUpdateRequest
from application.readings.sampling import SamplingService
from domain.sensors.errors import DeviceNotFoundError, InvalidSamplingError
from interfaces.api.dependencies import get_sampling_service


router = APIRouter(
    prefix="/api/devices",
    tags=["devices"]
)


# List devices
@router.get("")
def list_devices(
    family: str | None = None,
    role: str | None = None,
    session: Session = Depends(get_session)
):
    devices = DeviceFamilyService(
        DeviceRepository(session)
    ).list_devices(
        device_family=family,
        role=role
    )

    return [
        device_to_dto(device)
        for device in devices
    ]


# Create device family kit
@router.post("/provision", status_code=201)
def provision(
    family: str,
    session: Session = Depends(get_session)
):
    try:
        devices = DeviceFamilyService(
            DeviceRepository(session)
        ).provision_family(
            family
        )

        return [
            device_to_dto(device)
            for device in devices
        ]

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
