from uuid import UUID

from sqlalchemy.orm import Session

from infrastructure.persistence.models import LocationRow, ZoneRow
from domain.locations.errors import ConfigurationError


class LocationRepository:

    def __init__(self, session: Session):
        self.session = session


    # Create location + zones in one transaction
    def save_config(self, config):

        try:
            location = LocationRow(
                name=config.name
            )

            self.session.add(location)
            self.session.flush()

            zones = []

            for zone in config.zones:

                zone_row = ZoneRow(
                    location_id=location.id,
                    name=zone.name,
                    moisture_threshold_low=zone.moisture_threshold_low,
                    moisture_threshold_high=zone.moisture_threshold_high,
                    schedule=zone.schedule,
                )

                self.session.add(zone_row)
                zones.append(zone_row)


            self.session.commit()

            self.session.refresh(location)

            for zone in zones:
                self.session.refresh(zone)

            return location, zones


        except Exception:
            self.session.rollback()
            raise



    # Get all locations
    def list(self):

        return (
            self.session
            .query(LocationRow)
            .all()
        )



    # Get one location with zones
    def get_config(self, location_id: UUID):

        location = (
            self.session
            .query(LocationRow)
            .filter(
                LocationRow.id == location_id
            )
            .first()
        )

        if not location:
            return None


        zones = (
            self.session
            .query(ZoneRow)
            .filter(
                ZoneRow.location_id == location_id
            )
            .all()
        )

        return location, zones



    # Delete location
    def delete(self, location_id: UUID):

        location = (
            self.session
            .query(LocationRow)
            .filter(
                LocationRow.id == location_id
            )
            .first()
        )

        if not location:
            return False


        self.session.delete(location)
        self.session.commit()

        return True



    # Validate zone configuration
    def validate_zone(
        self,
        name: str,
        low: float,
        high: float
    ):

        if not name:
            raise ConfigurationError(
                "Zone name is required"
            )

        if low < 0 or low > 1:
            raise ConfigurationError(
                "Low threshold must be between 0 and 1"
            )

        if high < 0 or high > 1:
            raise ConfigurationError(
                "High threshold must be between 0 and 1"
            )

        if low >= high:
            raise ConfigurationError(
                "Low threshold must be smaller than high threshold"
            )



    # Add zone to existing location
    def add_zone(
        self,
        location_id: UUID,
        name: str,
        low: float,
        high: float,
        schedule: dict | None = None
    ):

        self.validate_zone(
            name,
            low,
            high
        )


        location = (
            self.session
            .query(LocationRow)
            .filter(
                LocationRow.id == location_id
            )
            .first()
        )

        if not location:
            raise ConfigurationError(
                "Location not found"
            )


        zone = ZoneRow(
            location_id=location_id,
            name=name,
            moisture_threshold_low=low,
            moisture_threshold_high=high,
            schedule=schedule,
        )


        self.session.add(zone)
        self.session.commit()
        self.session.refresh(zone)

        return zone



    # Update zone
    def update_zone(
        self,
        location_id: UUID,
        zone_id: UUID,
        name: str,
        low: float,
        high: float,
        schedule: dict | None = None
    ):

        self.validate_zone(
            name,
            low,
            high
        )


        zone = (
            self.session
            .query(ZoneRow)
            .filter(
                ZoneRow.id == zone_id,
                ZoneRow.location_id == location_id
            )
            .first()
        )


        if not zone:
            return None


        zone.name = name
        zone.moisture_threshold_low = low
        zone.moisture_threshold_high = high
        zone.schedule = schedule


        self.session.commit()
        self.session.refresh(zone)

        return zone



    # Delete zone
    def delete_zone(
        self,
        location_id: UUID,
        zone_id: UUID
    ):

        zone = (
            self.session
            .query(ZoneRow)
            .filter(
                ZoneRow.id == zone_id,
                ZoneRow.location_id == location_id
            )
            .first()
        )


        if not zone:
            return False


        # Prevent deleting the last zone
        remaining = (
            self.session
            .query(ZoneRow)
            .filter(
                ZoneRow.location_id == location_id
            )
            .count()
        )

        if remaining <= 1:
            raise ConfigurationError(
                "Cannot delete the last zone"
            )


        self.session.delete(zone)
        self.session.commit()

        return True