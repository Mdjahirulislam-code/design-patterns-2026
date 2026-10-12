from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class StrategyOptionDto(BaseModel):
    key: str = Field(examples=["conservative"])
    label: str = Field(examples=["Conservative"])
    description: str


class StrategyUpdateRequest(BaseModel):
    """Body of PUT /api/locations/{location_id}/automation."""

    strategy_key: str = Field(examples=["conservative"], description="conservative or aggressive")


class AutomationRuleDto(BaseModel):
    location_id: UUID
    strategy_key: str = Field(examples=["conservative"])
    is_default: bool = Field(
        description="True when nothing is saved yet and the default strategy is used"
    )
    updated_at: datetime | None = None


class ZoneRecommendationDto(BaseModel):
    zone_id: UUID
    zone_name: str
    action: str = Field(examples=["wait"])
    reason: str = Field(examples=["Moisture 0.40 is within 0.25–0.45"])
    score: float | None = None
    moisture: float | None = Field(None, description="Latest moisture from this zone's sensors")
    light: float | None = Field(None, description="Latest light from this zone's sensors")
    moisture_threshold_low: float
    moisture_threshold_high: float


class RecommendationDto(BaseModel):
    """Result of POST /api/locations/{location_id}/automation/evaluate."""

    location_id: UUID
    strategy_key: str = Field(examples=["conservative"])
    action: str = Field(examples=["wait"], description="irrigate if any zone needs water, else wait")
    reason: str = Field(examples=["Moisture 0.40 is within 0.25–0.45"])
    evaluated_at: datetime
    zones: list[ZoneRecommendationDto] = Field(default_factory=list)
