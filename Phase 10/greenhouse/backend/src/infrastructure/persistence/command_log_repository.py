"""Phase 10 persistence: command_log (append only)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.commands.record import CommandLogEntry
from infrastructure.persistence.models import CommandLogRow


class CommandLogRepository:

    def __init__(self, session: Session):
        self.session = session


    def insert(
        self,
        command_type: str,
        device_id: UUID,
        payload: dict,
        status: str,
        error_message: str | None,
    ) -> CommandLogEntry:

        row = CommandLogRow(
            command_type=command_type,
            device_id=device_id,
            payload=dict(payload or {}),
            status=status,
            error_message=error_message,
        )

        try:

            self.session.add(row)
            self.session.commit()
            self.session.refresh(row)

            return self._to_domain(row)

        except Exception:

            self.session.rollback()
            raise


    def list_recent(self, limit: int = 50) -> list[CommandLogEntry]:
        """Newest first."""

        query = (
            select(CommandLogRow)
            .order_by(
                CommandLogRow.created_at.desc(),
                CommandLogRow.id
            )
            .limit(limit)
        )

        return [
            self._to_domain(row)
            for row in self.session.scalars(query).all()
        ]


    def _to_domain(self, row: CommandLogRow) -> CommandLogEntry:

        return CommandLogEntry(
            id=row.id,
            command_type=row.command_type,
            device_id=row.device_id,
            payload=dict(row.payload or {}),
            status=row.status,
            error_message=row.error_message,
            created_at=row.created_at,
        )
