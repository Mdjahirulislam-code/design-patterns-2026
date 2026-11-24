"""Alert rows as plain data (Phase 11)."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_CRITICAL = "critical"

STATUS_ACTIVE = "active"
STATUS_RESOLVED = "resolved"
STATUS_ALL = "all"
ALERT_STATUSES = (STATUS_ACTIVE, STATUS_RESOLVED)


class InvalidAlertFilterError(ValueError):
    """Bad filter on the alert list (HTTP 400)."""


@dataclass(frozen=True, slots=True)
class Alert:
    id: UUID
    location_id: UUID | None
    zone_id: UUID | None
    device_id: UUID | None
    severity: str
    message: str
    event_type: str
    status: str
    created_at: datetime
    acknowledged_at: datetime | None = None
