"""The saved strategy choice of one location."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class StrategyRule:
    location_id: UUID
    strategy_key: str
    parameters: dict = field(default_factory=dict)
    updated_at: datetime | None = None
