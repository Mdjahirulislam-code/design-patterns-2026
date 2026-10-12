"""Phase 6 — Strategy: choose an automation strategy per location and evaluate it.

The router only maps HTTP to the service. It never checks which strategy is
active; that is resolved by get_strategy(key) inside the application.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from application.automation.dto import (
    AutomationRuleDto,
    RecommendationDto,
    StrategyOptionDto,
    StrategyUpdateRequest,
)
from application.automation.service import AutomationService
from domain.automation.errors import LocationNotFoundError, UnknownStrategyError
from interfaces.api.dependencies import get_automation_service

router = APIRouter(prefix="/api", tags=["automation"])

_ERRORS = {
    400: {"description": "Unknown strategy key"},
    404: {"description": "Location not found"},
}


@router.get(
    "/automation/strategies",
    response_model=list[StrategyOptionDto],
    summary="List available automation strategies",
)
def list_strategies() -> list[StrategyOptionDto]:
    return AutomationService.list_strategies()


@router.get(
    "/locations/{location_id}/automation",
    response_model=AutomationRuleDto,
    summary="Get the saved strategy of a location",
    responses={404: _ERRORS[404]},
)
def get_location_strategy(
    location_id: UUID,
    service: AutomationService = Depends(get_automation_service),
) -> AutomationRuleDto:
    try:
        return service.get_rule(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put(
    "/locations/{location_id}/automation",
    response_model=AutomationRuleDto,
    summary="Save the strategy of a location",
    responses=_ERRORS,
)
def set_location_strategy(
    location_id: UUID,
    request: StrategyUpdateRequest,
    service: AutomationService = Depends(get_automation_service),
) -> AutomationRuleDto:
    try:
        return service.set_strategy(location_id, request.strategy_key)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnknownStrategyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/locations/{location_id}/automation/evaluate",
    response_model=RecommendationDto,
    summary="Evaluate a location with its saved strategy",
    responses=_ERRORS,
)
def evaluate_location(
    location_id: UUID,
    service: AutomationService = Depends(get_automation_service),
) -> RecommendationDto:
    """Uses the persisted strategy key, the zones' thresholds and the latest
    stored readings of the sensors assigned to each zone."""
    try:
        return service.evaluate(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnknownStrategyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
