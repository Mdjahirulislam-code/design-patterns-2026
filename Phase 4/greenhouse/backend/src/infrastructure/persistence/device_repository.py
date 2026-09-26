from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.persistence.models import DeviceRow
from domain.devices.entity import Device


class DeviceRepository:

    def __init__(self, session: Session):
        self.session = session


    def save_devices(self, devices: list[Device]):

        rows = []

        try:

            for device in devices:

                row = DeviceRow(
                    device_type=device.device_type,
                    role=device.role,
                    device_family=device.device_family,
                    display_name=device.display_name,
                    default_config=device.default_config,
                )

                self.session.add(row)
                rows.append(row)


            self.session.commit()


            for row in rows:
                self.session.refresh(row)


            return [
                self._to_domain(row)
                for row in rows
            ]


        except Exception as e:

            self.session.rollback()

            print("SAVE DEVICES ERROR:")
            print(str(e))

            raise e



    def list_devices(
        self,
        device_family=None,
        role=None
    ):

        query = select(DeviceRow)


        if device_family:
            query = query.where(
                DeviceRow.device_family == device_family
            )


        if role:
            query = query.where(
                DeviceRow.role == role
            )


        rows = self.session.scalars(query).all()


        return [
            self._to_domain(row)
            for row in rows
        ]



    def list_sensors(self):
        """
        Compatibility method for Phase 2 sensor API.
        Returns only sensor devices.
        """
        return self.list_devices(role="sensor")



    def save_sensor(self, sensor):
        """
        Compatibility method for Phase 2 sensor creation.
        Converts old sensor objects into Device rows.
        """

        row = DeviceRow(
            device_type=sensor.sensor_type,
            role="sensor",
            device_family="simulation",
            display_name=sensor.display_name,
            default_config=sensor.config,
        )

        try:

            self.session.add(row)
            self.session.commit()
            self.session.refresh(row)

            return self._to_domain(row)

        except Exception as e:

            self.session.rollback()

            print("SAVE SENSOR ERROR:")
            print(str(e))

            raise e



    def _to_domain(self, row: DeviceRow):

        return Device(
            id=row.id,
            device_type=row.device_type,
            role=row.role,
            device_family=row.device_family,
            display_name=row.display_name or row.device_type,
            default_config=dict(row.default_config or {})
        )