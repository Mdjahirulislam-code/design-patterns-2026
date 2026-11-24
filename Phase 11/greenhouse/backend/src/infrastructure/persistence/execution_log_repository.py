"""Phase 9 persistence: actuator_execution_log (append only)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.actuators.execution import ActuatorExecution
from infrastructure.persistence.models import ActuatorExecutionLogRow


class ExecutionLogRepository:

    def __init__(self, session: Session):
        self.session = session


    def insert(
        self,
        device_id: UUID,
        success: bool,
        policy_applied: list[str],
        message: str | None,
    ) -> ActuatorExecution:
        """Append one attempt. Called by the logging decorator for every apply()."""

        row = ActuatorExecutionLogRow(
            device_id=device_id,
            success=success,
            policy_applied=list(policy_applied),
            message=message,
        )

        try:

            self.session.add(row)
            self.session.commit()
            self.session.refresh(row)

            return self._to_domain(row)

        except Exception:

            self.session.rollback()
            raise


    def list_recent(self, limit: int = 20) -> list[ActuatorExecution]:
        """Newest first."""

        query = (
            select(ActuatorExecutionLogRow)
            .order_by(
                ActuatorExecutionLogRow.created_at.desc(),
                ActuatorExecutionLogRow.id
            )
            .limit(limit)
        )

        return [
            self._to_domain(row)
            for row in self.session.scalars(query).all()
        ]


    def latest_for_device(self, device_id: UUID) -> ActuatorExecution | None:

        query = (
            select(ActuatorExecutionLogRow)
            .where(ActuatorExecutionLogRow.device_id == device_id)
            .order_by(ActuatorExecutionLogRow.created_at.desc())
            .limit(1)
        )

        row = self.session.scalars(query).first()

        return self._to_domain(row) if row else None


    def _to_domain(self, row: ActuatorExecutionLogRow) -> ActuatorExecution:

        return ActuatorExecution(
            id=row.id,
            device_id=row.device_id,
            success=row.success,
            policy_applied=list(row.policy_applied or []),
            message=row.message,
            created_at=row.created_at,
        )
