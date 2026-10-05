from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.db import get_session

from application.locations.dto import LocationRequest, ZoneRequest
from application.locations.zone_assignment_service import ZoneAssignmentService

from domain.locations.config_builder import LocationConfigBuilder
from domain.locations.errors import ConfigurationError

from infrastructure.persistence.location_repository import LocationRepository


router = APIRouter(
    prefix="/api/locations",
    tags=["locations"]
)


# --------------------------------------------------
# Create location configuration
# --------------------------------------------------

@router.post("/config", status_code=201)
def create(
    req: LocationRequest,
    session: Session = Depends(get_session)
):
    try:
        builder = (
            LocationConfigBuilder()
            .with_location_name(req.location_name)
        )

        for z in req.zones:
            builder.add_zone(
                z.name,
                z.moisture_threshold_low,
                z.moisture_threshold_high,
                z.schedule
            )

        config = builder.build()

        location, zones = LocationRepository(session).save_config(config)

        return {
            "location": {
                "id": str(location.id),
                "name": location.name
            },
            "zones": [
                {
                    "id": str(zone.id),
                    "location_id": str(zone.location_id),
                    "name": zone.name
                }
                for zone in zones
            ]
        }

    except ConfigurationError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# --------------------------------------------------
# List locations
# --------------------------------------------------

@router.get("")
def list_locations(
    session: Session = Depends(get_session)
):
    locations = LocationRepository(session).list()

    return [
        {
            "id": str(location.id),
            "name": location.name
        }
        for location in locations
    ]


# --------------------------------------------------
# Get location configuration
# --------------------------------------------------

@router.get("/{location_id}/config")
def get_config(
    location_id: UUID,
    session: Session = Depends(get_session)
):
    result = LocationRepository(session).get_config(location_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found"
        )

    location, zones = result

    return {
        "location": {
            "id": str(location.id),
            "name": location.name
        },
        "zones": [
            {
                "id": str(zone.id),
                "location_id": str(zone.location_id),
                "name": zone.name,
                "moisture_threshold_low": zone.moisture_threshold_low,
                "moisture_threshold_high": zone.moisture_threshold_high,
                "schedule": zone.schedule
            }
            for zone in zones
        ]
    }


# --------------------------------------------------
# Delete location
# --------------------------------------------------

@router.delete("/{location_id}", status_code=204)
def delete_location(
    location_id: UUID,
    session: Session = Depends(get_session)
):
    deleted = LocationRepository(session).delete(location_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Location not found"
        )

    return None


# --------------------------------------------------
# Add zone
# --------------------------------------------------

@router.post("/{location_id}/zones", status_code=201)
def add_zone(
    location_id: UUID,
    req: ZoneRequest,
    session: Session = Depends(get_session)
):
    try:

        zone = LocationRepository(session).add_zone(
            location_id,
            req.name,
            req.moisture_threshold_low,
            req.moisture_threshold_high,
            req.schedule
        )

        if zone is None:
            raise HTTPException(
                status_code=404,
                detail="Location not found"
            )

        return {
            "id": str(zone.id),
            "location_id": str(zone.location_id),
            "name": zone.name,
            "moisture_threshold_low": zone.moisture_threshold_low,
            "moisture_threshold_high": zone.moisture_threshold_high,
            "schedule": zone.schedule
        }

    except ConfigurationError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# --------------------------------------------------
# Update zone
# --------------------------------------------------

@router.patch("/{location_id}/zones/{zone_id}")
def update_zone(
    location_id: UUID,
    zone_id: UUID,
    req: ZoneRequest,
    session: Session = Depends(get_session)
):
    try:

        zone = LocationRepository(session).update_zone(
            location_id,
            zone_id,
            req.name,
            req.moisture_threshold_low,
            req.moisture_threshold_high,
            req.schedule
        )

        if zone is None:
            raise HTTPException(
                status_code=404,
                detail="Zone not found"
            )

        return {
            "id": str(zone.id),
            "location_id": str(zone.location_id),
            "name": zone.name,
            "moisture_threshold_low": zone.moisture_threshold_low,
            "moisture_threshold_high": zone.moisture_threshold_high,
            "schedule": zone.schedule
        }

    except ConfigurationError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# --------------------------------------------------
# Delete zone
# --------------------------------------------------

@router.delete("/{location_id}/zones/{zone_id}", status_code=204)
def delete_zone(
    location_id: UUID,
    zone_id: UUID,
    session: Session = Depends(get_session)
):

    try:

        deleted = LocationRepository(session).delete_zone(
            location_id,
            zone_id
        )

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Zone not found"
            )

        return None

    except ConfigurationError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# --------------------------------------------------
# List devices inside a zone
# --------------------------------------------------

@router.get("/{location_id}/zones/{zone_id}/devices")
def list_zone_devices(
    location_id: UUID,
    zone_id: UUID,
    session: Session = Depends(get_session)
):

    devices = ZoneAssignmentService(session).list_devices(
        location_id,
        zone_id
    )

    return [
        {
            "id": str(device.id),
            "device_type": device.device_type,
            "role": device.role,
            "device_family": device.device_family,
            "display_name": device.display_name
        }
        for device in devices
    ]