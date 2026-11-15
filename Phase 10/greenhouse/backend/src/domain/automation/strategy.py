"""Strategy pattern: AutomationStrategy and the concrete irrigation policies.

Every strategy gets the same plain LocationAutomationContext and returns a
Recommendation. The strategy only recommends; it never calls an actuator.

Documented difference on the same context:

| moisture (zone low 0.25, high 0.45) | conservative | aggressive |
|-------------------------------------|--------------|------------|
| 0.20 (below low)                    | irrigate     | irrigate   |
| 0.35 (inside the band)              | wait         | irrigate   |
| 0.45 or more (at / above high)      | wait         | wait       |

Conservative saves water: it waits until the soil is below the zone's low
threshold. Aggressive keeps the soil near the top of the band: it irrigates
as soon as moisture is below the zone's high threshold.
"""

from abc import ABC, abstractmethod

from domain.automation.context import (
    ACTION_IRRIGATE,
    ACTION_WAIT,
    LocationAutomationContext,
    Recommendation,
)
from domain.automation.errors import UnknownStrategyError


def _fmt(value: float) -> str:
    return f"{value:.2f}"


def _band(context: LocationAutomationContext) -> str:
    return f"{_fmt(context.low)}–{_fmt(context.high)}"


def _missing_reading(context: LocationAutomationContext) -> Recommendation | None:
    """Shared rule: without a reading from this zone there is nothing to decide."""
    if not context.has_moisture_sensor:
        return Recommendation(ACTION_WAIT, "No moisture sensor in this zone")
    if context.moisture is None:
        return Recommendation(ACTION_WAIT, "No moisture reading stored for this zone yet")
    return None


def _deficit(moisture: float, target: float, context: LocationAutomationContext) -> float:
    """How far below the target the soil is, as 0..1 of the zone band width."""
    width = context.high - context.low
    return round(min(max((target - moisture) / width, 0.0), 1.0), 3)


class AutomationStrategy(ABC):
    key: str
    label: str
    description: str

    @abstractmethod
    def decide(self, context: LocationAutomationContext) -> Recommendation:
        raise NotImplementedError


class ConservativeMoistureStrategy(AutomationStrategy):
    key = "conservative"
    label = "Conservative"
    description = "Irrigate only when moisture is below the zone's low threshold."

    def decide(self, context: LocationAutomationContext) -> Recommendation:
        missing = _missing_reading(context)
        if missing is not None:
            return missing

        moisture = context.moisture
        if moisture < context.low:
            return Recommendation(
                ACTION_IRRIGATE,
                f"Moisture {_fmt(moisture)} is below the low threshold {_fmt(context.low)}",
                _deficit(moisture, context.low, context),
            )
        if moisture > context.high:
            return Recommendation(
                ACTION_WAIT,
                f"Moisture {_fmt(moisture)} is above the high threshold {_fmt(context.high)}",
                0.0,
            )
        return Recommendation(
            ACTION_WAIT,
            f"Moisture {_fmt(moisture)} is within {_band(context)}",
            0.0,
        )


class AggressiveMoistureStrategy(AutomationStrategy):
    key = "aggressive"
    label = "Aggressive"
    description = "Irrigate whenever moisture is below the zone's high threshold."

    def decide(self, context: LocationAutomationContext) -> Recommendation:
        missing = _missing_reading(context)
        if missing is not None:
            return missing

        moisture = context.moisture
        if moisture < context.low:
            return Recommendation(
                ACTION_IRRIGATE,
                f"Moisture {_fmt(moisture)} is below the low threshold {_fmt(context.low)}",
                _deficit(moisture, context.high, context),
            )
        if moisture < context.high:
            return Recommendation(
                ACTION_IRRIGATE,
                f"Moisture {_fmt(moisture)} is below the high threshold {_fmt(context.high)}, "
                "topping up early",
                _deficit(moisture, context.high, context),
            )
        return Recommendation(
            ACTION_WAIT,
            f"Moisture {_fmt(moisture)} has reached the high threshold {_fmt(context.high)}",
            0.0,
        )


# Registry: the only place that maps a key to a class.
# Adding a third strategy = one new class + one line here.
_STRATEGIES: dict[str, type[AutomationStrategy]] = {
    ConservativeMoistureStrategy.key: ConservativeMoistureStrategy,
    AggressiveMoistureStrategy.key: AggressiveMoistureStrategy,
}

DEFAULT_STRATEGY_KEY = ConservativeMoistureStrategy.key


def available_strategies() -> list[AutomationStrategy]:
    return [cls() for cls in _STRATEGIES.values()]


def normalize_key(key: str) -> str:
    return (key or "").strip().lower()


def get_strategy(key: str) -> AutomationStrategy:
    """Resolve a key. Unknown keys are rejected here, before any decide()."""
    strategy_class = _STRATEGIES.get(normalize_key(key))
    if strategy_class is None:
        allowed = ", ".join(sorted(_STRATEGIES))
        raise UnknownStrategyError(
            f"Unknown strategy '{key}'. Expected one of: {allowed}."
        )
    return strategy_class()
