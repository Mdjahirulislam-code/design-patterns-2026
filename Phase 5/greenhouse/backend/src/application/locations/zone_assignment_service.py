from uuid import UUID

from infrastructure.persistence.models import DeviceRow, ZoneRow


class ZoneAssignmentService:

    def __init__(self, session):
        self.session = session


    def assign(
        self,
        device_id: UUID,
        zone_id: UUID | None
    ) -> None:

        device = (
            self.session
            .query(DeviceRow)
            .filter(DeviceRow.id == device_id)
            .first()
        )

        if device is None:
            raise ValueError("Device not found")


        # Remove device from zone
        if zone_id is None:

            device.zone_id = None
            device.location_id = None

            self.session.commit()
            self.session.refresh(device)

            return


        # Find zone
        zone = (
            self.session
            .query(ZoneRow)
            .filter(ZoneRow.id == zone_id)
            .first()
        )

        if zone is None:
            raise ValueError("Zone not found")


        # Assign zone and copy location
        device.zone_id = zone.id
        device.location_id = zone.location_id


        self.session.commit()
        self.session.refresh(device)



    def list_devices(
        self,
        location_id: UUID,
        zone_id: UUID
    ):

        return (
            self.session
            .query(DeviceRow)
            .filter(
                DeviceRow.location_id == location_id,
                DeviceRow.zone_id == zone_id
            )
            .all()
        )