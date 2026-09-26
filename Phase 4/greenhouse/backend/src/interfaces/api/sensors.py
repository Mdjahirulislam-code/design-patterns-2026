"""REST endpoints for creating and listing persisted sensors."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from application.sensors.service import SensorService
from domain.sensors.entity import Sensor
from infrastructure.db import get_session
from infrastructure.persistence.device_repository import DeviceRepository

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


class SensorCreateRequest(BaseModel):
    type: str = Field(examples=["moisture"])
    display_name: str | None = None


class SensorResponse(BaseModel):
    id: UUID
    device_type: str
    display_name: str
    default_config: dict[str, Any]


def _service(session: Session) -> SensorService:
    return SensorService(DeviceRepository(session))


def _to_response(sensor: Sensor) -> SensorResponse:
    if sensor.id is None:
        raise RuntimeError("Persisted sensor is missing an id")
    return SensorResponse(
        id=sensor.id,
        device_type=sensor.device_type,
        display_name=sensor.display_name,
        default_config=sensor.default_config,
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
        sensor = _service(session).create_sensor(payload.type, payload.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(sensor)
