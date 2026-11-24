"""AlertQueryService: the alert list behind GET /api/alerts."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from application.alerts.dto import AlertDto
from domain.alerts import ALERT_STATUSES, STATUS_ALL, Alert, InvalidAlertFilterError


class AlertReader(Protocol):
    def list(
        self,
        status: str | None,
        location_id: UUID | None,
        zone_id: UUID | None,
        since: datetime | None,
        limit: int,
    ) -> list[Alert]: ...


def alert_to_dto(alert: Alert) -> AlertDto:
    return AlertDto(
        id=alert.id,
        location_id=alert.location_id,
        zone_id=alert.zone_id,
        device_id=alert.device_id,
        severity=alert.severity,
        message=alert.message,
        event_type=alert.event_type,
        status=alert.status,
        created_at=alert.created_at,
    )


class AlertQueryService:
    def __init__(self, alerts: AlertReader) -> None:
        self._alerts = alerts

    def list(
        self,
        status: str = "active",
        location_id: UUID | None = None,
        zone_id: UUID | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[AlertDto]:
        key = (status or "").strip().lower()
        if key != STATUS_ALL and key not in ALERT_STATUSES:
            raise InvalidAlertFilterError(
                f"Unknown status '{status}'. Expected one of: active, resolved, all."
            )
        rows = self._alerts.list(
            None if key == STATUS_ALL else key, location_id, zone_id, since, limit
        )
        return [alert_to_dto(row) for row in rows]
