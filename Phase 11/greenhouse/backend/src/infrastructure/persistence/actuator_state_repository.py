"""Phase 8 persistence: one lifecycle row per actuator in actuator_states."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.actuators.record import ActuatorStateRecord
from infrastructure.persistence.models import ActuatorStateRow


class ActuatorStateRepository:

    def __init__(self, session: Session):
        self.session = session


    def get(self, device_id: UUID) -> ActuatorStateRecord | None:

        row = self.session.get(ActuatorStateRow, device_id)

        return self._to_domain(row) if row else None


    def get_many(self, device_ids: list[UUID]) -> dict[UUID, str]:
        """States of many actuators in one query."""

        if not device_ids:
            return {}

        rows = self.session.scalars(
            select(ActuatorStateRow).where(
                ActuatorStateRow.device_id.in_(device_ids)
            )
        ).all()

        return {
            row.device_id: row.state
            for row in rows
        }


    def save(self, device_id: UUID, state: str) -> ActuatorStateRecord:
        """Insert or update the row. Only called after the domain allowed the move."""

        try:

            row = self.session.get(ActuatorStateRow, device_id)

            if row is None:
                row = ActuatorStateRow(device_id=device_id, state=state)
                self.session.add(row)
            else:
                row.state = state
                row.updated_at = datetime.now(timezone.utc)

            self.session.commit()
            self.session.refresh(row)

            return self._to_domain(row)

        except Exception:

            self.session.rollback()
            raise


    def _to_domain(self, row: ActuatorStateRow) -> ActuatorStateRecord:

        return ActuatorStateRecord(
            device_id=row.device_id,
            state=row.state,
            updated_at=row.updated_at,
        )
