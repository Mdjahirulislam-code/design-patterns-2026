"""Phase 11 persistence: the alerts table.

Only AlertPersistenceSubscriber writes here. Publishers never import this file.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.alerts import STATUS_ACTIVE, Alert
from infrastructure.persistence.models import AlertRow


class AlertRepository:

    def __init__(self, session: Session):
        self.session = session


    def insert(
        self,
        *,
        location_id: UUID | None,
        zone_id: UUID | None,
        device_id: UUID | None,
        severity: str,
        message: str,
        event_type: str,
    ) -> Alert:

        row = AlertRow(
            location_id=location_id,
            zone_id=zone_id,
            device_id=device_id,
            severity=severity,
            message=message,
            event_type=event_type,
            status=STATUS_ACTIVE,
        )

        try:

            self.session.add(row)
            self.session.commit()
            self.session.refresh(row)

            return self._to_domain(row)

        except Exception:

            self.session.rollback()
            raise


    def list(
        self,
        status: str | None,
        location_id: UUID | None,
        zone_id: UUID | None,
        since: datetime | None,
        limit: int,
    ) -> list[Alert]:
        """Newest first. `status=None` means every status."""

        query = select(AlertRow)

        if status is not None:
            query = query.where(AlertRow.status == status)
        if location_id is not None:
            query = query.where(AlertRow.location_id == location_id)
        if zone_id is not None:
            query = query.where(AlertRow.zone_id == zone_id)
        if since is not None:
            query = query.where(AlertRow.created_at >= since)

        query = query.order_by(AlertRow.created_at.desc(), AlertRow.id).limit(limit)

        return [
            self._to_domain(row)
            for row in self.session.scalars(query).all()
        ]


    def _to_domain(self, row: AlertRow) -> Alert:

        return Alert(
            id=row.id,
            location_id=row.location_id,
            zone_id=row.zone_id,
            device_id=row.device_id,
            severity=row.severity,
            message=row.message,
            event_type=row.event_type,
            status=row.status,
            created_at=row.created_at,
            acknowledged_at=row.acknowledged_at,
        )
