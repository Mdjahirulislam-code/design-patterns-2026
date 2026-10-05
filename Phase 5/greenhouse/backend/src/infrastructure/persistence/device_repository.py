from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.persistence.models import DeviceRow
from domain.devices.entity import MIN_SAMPLING_INTERVAL_SECONDS, Device


def _initial_interval(default_config: dict) -> int | None:
    """Creators may put sampling_interval_seconds in default_config.

    It is copied into the column once, when the row is created. After that the
    column is the source of truth and default_config is not read for sampling.
    """
    value = (default_config or {}).get("sampling_interval_seconds")

    if isinstance(value, bool) or not isinstance(value, int):
        return None

    return max(value, MIN_SAMPLING_INTERVAL_SECONDS)


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

                interval = _initial_interval(device.default_config)
                if interval is not None:
                    row.sampling_interval_seconds = interval

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


        query = query.order_by(
            DeviceRow.created_at,
            DeviceRow.id
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



    # Phase 5: load one device
    def get(self, device_id: UUID) -> Device | None:

        row = self.session.get(DeviceRow, device_id)

        if row is None:
            return None

        return self._to_domain(row)



    # Phase 5: sampling settings
    def update_sampling(
        self,
        device_id: UUID,
        sampling_interval_seconds: int,
        tracking_enabled: bool
    ) -> Device | None:

        row = self.session.get(DeviceRow, device_id)

        if row is None:
            return None

        try:

            row.sampling_interval_seconds = sampling_interval_seconds
            row.tracking_enabled = tracking_enabled

            self.session.commit()
            self.session.refresh(row)

            return self._to_domain(row)

        except Exception:

            self.session.rollback()
            raise



    def save_sensor(self, sensor):
        """
        Compatibility method for Phase 2 sensor creation.
        Converts old sensor objects into Device rows.
        """

        row = DeviceRow(
            device_type=sensor.device_type,
            role="sensor",
            device_family="simulation",
            display_name=sensor.display_name,
            default_config=sensor.default_config,
        )

        interval = _initial_interval(sensor.default_config)
        if interval is not None:
            row.sampling_interval_seconds = interval

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
            default_config=dict(row.default_config or {}),
            zone_id=row.zone_id,
            sampling_interval_seconds=row.sampling_interval_seconds,
            tracking_enabled=row.tracking_enabled,
        )
