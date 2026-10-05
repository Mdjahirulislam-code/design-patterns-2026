"""Readings repository. Only ReadingIngest calls `insert`."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.sensors.reading import Reading
from infrastructure.persistence.models import ReadingRow


class ReadingRepository:

    def __init__(self, session: Session):
        self.session = session


    def insert(self, reading: Reading) -> Reading:

        row = ReadingRow(
            device_id=reading.device_id,
            value=Decimal(str(reading.value)),
            unit=reading.unit,
            source=reading.source,
            recorded_at=reading.recorded_at,
        )

        try:

            self.session.add(row)
            self.session.commit()
            self.session.refresh(row)

            return self._to_domain(row)

        except Exception:

            self.session.rollback()
            raise


    def list_for_device(self, device_id: UUID, limit: int = 20) -> list[Reading]:
        """Newest first. Uses the (device_id, recorded_at DESC) index."""

        query = (
            select(ReadingRow)
            .where(ReadingRow.device_id == device_id)
            .order_by(ReadingRow.recorded_at.desc())
            .limit(limit)
        )

        return [
            self._to_domain(row)
            for row in self.session.scalars(query).all()
        ]


    def latest_for_device(self, device_id: UUID) -> Reading | None:

        rows = self.list_for_device(device_id, limit=1)

        return rows[0] if rows else None


    def _to_domain(self, row: ReadingRow) -> Reading:

        return Reading(
            device_id=row.device_id,
            value=float(row.value),
            unit=row.unit,
            source=row.source,
            recorded_at=row.recorded_at,
        )
