"""Phase 7 — Facade: one overview read API for the dashboard.

The handler's only collaborator is LocationOverviewFacade. It does not import
any repository or the automation service.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from application.overview.dto import LocationOverviewDto
from application.overview.facade import LocationOverviewFacade
from domain.locations.errors import LocationNotFoundError
from interfaces.api.dependencies import get_overview_facade

router = APIRouter(prefix="/api/locations", tags=["overview"])


@router.get(
    "/{location_id}/overview",
    response_model=LocationOverviewDto,
    summary="Overview of one location",
    responses={404: {"description": "Location not found"}},
)
def get_location_overview(
    location_id: UUID,
    facade: LocationOverviewFacade = Depends(get_overview_facade),
) -> LocationOverviewDto:
    """Location, assigned device counts, every zone with its assigned devices and
    their newest readings, the saved strategy key and the recommendation computed
    by evaluate on this request. No saved strategy is still 200 with nulls."""
    try:
        return facade.get_overview(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
