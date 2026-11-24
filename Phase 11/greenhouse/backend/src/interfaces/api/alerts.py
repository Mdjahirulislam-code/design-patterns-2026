"""Phase 11 — Observer: the alert list behind the dashboard event feed.

Alerts are written only by AlertPersistenceSubscriber. This router only reads.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from application.alerts.dto import AlertDto
from application.alerts.service import AlertQueryService
from domain.alerts import InvalidAlertFilterError
from interfaces.api.dependencies import get_alert_service

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get(
    "",
    response_model=list[AlertDto],
    summary="List alerts (newest first)",
    responses={400: {"description": "Unknown status"}},
)
def list_alerts(
    status: str = Query("active", description="active, resolved or all"),
    location_id: UUID | None = Query(None, description="Only alerts of this location"),
    zone_id: UUID | None = Query(None, description="Only alerts of this zone"),
    since: datetime | None = Query(None, description="Only alerts created at or after this time"),
    limit: int = Query(50, ge=1, le=200, description="How many rows to return"),
    service: AlertQueryService = Depends(get_alert_service),
) -> list[AlertDto]:
    try:
        return service.list(status, location_id, zone_id, since, limit)
    except InvalidAlertFilterError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
