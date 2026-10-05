"""REST endpoints for sensors: create, list, read now and reading history."""

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from application.readings.dto import ReadingDto
from application.readings.service import ReadingIngest
from application.sensors.service import SensorService
from domain.sensors.errors import DeviceNotFoundError, SensorReadError
from infrastructure.db import get_session
from infrastructure.persistence.device_repository import DeviceRepository
from interfaces.api.dependencies import get_reading_ingest

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


class SensorCreateRequest(BaseModel):
    type: str = Field(examples=["moisture"])
    display_name: str | None = None
    # Phase 5: "vendor" stores default_config.vendor_stub = true
    adapter: Literal["simulation", "vendor"] = "simulation"


class SensorResponse(BaseModel):
    id: UUID
    device_type: str
    role: str = "sensor"
    device_family: str = "simulation"
    display_name: str
    default_config: dict[str, Any]
    zone_id: UUID | None = None
    # Phase 5
    sampling_interval_seconds: int = 300
    tracking_enabled: bool = True


def _service(session: Session) -> SensorService:
    return SensorService(DeviceRepository(session))


def _to_response(sensor) -> SensorResponse:
    if sensor.id is None:
        raise RuntimeError("Persisted sensor is missing an id")
    return SensorResponse(
        id=sensor.id,
        device_type=sensor.device_type,
        role=sensor.role,
        device_family=sensor.device_family,
        display_name=sensor.display_name,
        default_config=sensor.default_config,
        zone_id=sensor.zone_id,
        sampling_interval_seconds=sensor.sampling_interval_seconds,
        tracking_enabled=sensor.tracking_enabled,
    )


@router.get("", response_model=list[SensorResponse], summary="List sensors")
def list_sensors(session: Session = Depends(get_session)) -> list[SensorResponse]:
    return [_to_response(sensor) for sensor in _service(session).list_sensors()]


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a sensor",
)
def create_sensor(
    payload: SensorCreateRequest,
    session: Session = Depends(get_session),
) -> SensorResponse:
    try:
        sensor = _service(session).create_sensor(
            payload.type, payload.display_name, payload.adapter
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(sensor)


# --------------------------------------------------
# Phase 5 — Adapter: read now + history
# --------------------------------------------------

@router.post(
    "/{sensor_id}/read",
    response_model=ReadingDto,
    status_code=status.HTTP_201_CREATED,
    summary="Read a sensor now and store the reading",
    responses={
        400: {"description": "The adapter could not read this device"},
        404: {"description": "Device not found"},
    },
)
def read_sensor(
    sensor_id: UUID,
    ingest: ReadingIngest = Depends(get_reading_ingest),
) -> ReadingDto:
    """Runs the adapter selected for this sensor, appends one row to
    `sensor_readings` and returns the normalized reading."""
    try:
        return ingest.take_reading(sensor_id)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SensorReadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/{sensor_id}/readings",
    response_model=list[ReadingDto],
    summary="List recent readings of a sensor (newest first)",
    responses={404: {"description": "Device not found"}},
)
def list_readings(
    sensor_id: UUID,
    limit: int = Query(20, ge=1, le=500, description="How many readings to return"),
    ingest: ReadingIngest = Depends(get_reading_ingest),
) -> list[ReadingDto]:
    try:
        return ingest.list_readings(sensor_id, limit)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SensorReadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
