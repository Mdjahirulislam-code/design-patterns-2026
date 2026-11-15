"""AutomationService: saves the strategy per location and evaluates a location.

Flow of evaluate():
1. location must exist (else LocationNotFoundError -> 404)
2. load the saved strategy key (default "conservative" when nothing is saved)
3. get_strategy(key) rejects an unknown key before any decide()
4. one LocationAutomationContext per zone: the zone's thresholds from `zones`
   plus the latest reading from sensors whose devices.zone_id is that zone
5. strategy.decide(context) for each zone, then map to DTOs

Strategies only receive plain context objects, never ORM rows.
"""

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from application.automation.dto import (
    AutomationRuleDto,
    RecommendationDto,
    StrategyOptionDto,
    ZoneRecommendationDto,
)
from domain.automation.context import (
    ACTION_IRRIGATE,
    ACTION_WAIT,
    LocationAutomationContext,
    Recommendation,
)
from domain.automation.errors import LocationNotFoundError
from domain.automation.rule import StrategyRule
from domain.automation.strategy import (
    DEFAULT_STRATEGY_KEY,
    available_strategies,
    get_strategy,
)
from domain.devices.entity import Device
from domain.locations.entity import ZoneThresholds
from domain.sensors.reading import Reading

MOISTURE_SENSOR = "moisture_sensor"
LIGHT_SENSOR = "light_sensor"


class LocationDirectory(Protocol):
    def exists(self, location_id: UUID) -> bool: ...

    def list_zones(self, location_id: UUID) -> list[ZoneThresholds]: ...


class AutomationRuleStore(Protocol):
    def get(self, location_id: UUID) -> StrategyRule | None: ...

    def upsert(self, location_id: UUID, strategy_key: str) -> StrategyRule: ...


class ZoneSensorDirectory(Protocol):
    def list_sensors_in_zone(self, zone_id: UUID) -> list[Device]: ...


class LatestReadings(Protocol):
    def latest_for_device(self, device_id: UUID) -> Reading | None: ...


class AutomationService:
    def __init__(
        self,
        locations: LocationDirectory,
        rules: AutomationRuleStore,
        sensors: ZoneSensorDirectory,
        readings: LatestReadings,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._locations = locations
        self._rules = rules
        self._sensors = sensors
        self._readings = readings
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    # ---------- strategy choice ----------

    @staticmethod
    def list_strategies() -> list[StrategyOptionDto]:
        return [
            StrategyOptionDto(key=s.key, label=s.label, description=s.description)
            for s in available_strategies()
        ]

    def get_rule(self, location_id: UUID) -> AutomationRuleDto:
        self._require_location(location_id)
        rule = self._rules.get(location_id)
        if rule is None:
            return AutomationRuleDto(
                location_id=location_id, strategy_key=DEFAULT_STRATEGY_KEY, is_default=True
            )
        return self._rule_to_dto(rule)

    def set_strategy(self, location_id: UUID, strategy_key: str) -> AutomationRuleDto:
        self._require_location(location_id)
        strategy = get_strategy(strategy_key)  # unknown key -> UnknownStrategyError (400)
        rule = self._rules.upsert(location_id, strategy.key)
        return self._rule_to_dto(rule)

    # ---------- evaluation ----------

    def evaluate(self, location_id: UUID) -> RecommendationDto:
        self._require_location(location_id)

        rule = self._rules.get(location_id)
        strategy_key = rule.strategy_key if rule else DEFAULT_STRATEGY_KEY
        strategy = get_strategy(strategy_key)  # checked before decide()

        zone_results: list[ZoneRecommendationDto] = []
        for context in self.build_contexts(location_id):
            recommendation = strategy.decide(context)
            zone_results.append(self._zone_to_dto(context, recommendation))

        action, reason = self._summarize(zone_results)
        return RecommendationDto(
            location_id=location_id,
            strategy_key=strategy.key,
            action=action,
            reason=reason,
            evaluated_at=self._clock(),
            zones=zone_results,
        )

    def build_contexts(self, location_id: UUID) -> list[LocationAutomationContext]:
        contexts = []
        for zone in self._locations.list_zones(location_id):
            sensors = self._sensors.list_sensors_in_zone(zone.zone_id)
            moisture_sensors = [s for s in sensors if s.device_type == MOISTURE_SENSOR]
            light_sensors = [s for s in sensors if s.device_type == LIGHT_SENSOR]

            contexts.append(
                LocationAutomationContext(
                    location_id=location_id,
                    zone_id=zone.zone_id,
                    zone_name=zone.name,
                    low=zone.moisture_threshold_low,
                    high=zone.moisture_threshold_high,
                    moisture=self._latest_value(moisture_sensors),
                    has_moisture_sensor=bool(moisture_sensors),
                    light=self._latest_value(light_sensors),
                )
            )
        return contexts

    # ---------- helpers ----------

    def _latest_value(self, sensors: list[Device]) -> float | None:
        """Newest reading among the given sensors, or None."""
        newest: Reading | None = None
        for sensor in sensors:
            reading = self._readings.latest_for_device(sensor.id)
            if reading is not None and (newest is None or reading.recorded_at > newest.recorded_at):
                newest = reading
        return newest.value if newest else None

    def _require_location(self, location_id: UUID) -> None:
        if not self._locations.exists(location_id):
            raise LocationNotFoundError(f"Location {location_id} not found")

    @staticmethod
    def _rule_to_dto(rule: StrategyRule) -> AutomationRuleDto:
        return AutomationRuleDto(
            location_id=rule.location_id,
            strategy_key=rule.strategy_key,
            is_default=False,
            updated_at=rule.updated_at,
        )

    @staticmethod
    def _zone_to_dto(
        context: LocationAutomationContext, recommendation: Recommendation
    ) -> ZoneRecommendationDto:
        return ZoneRecommendationDto(
            zone_id=context.zone_id,
            zone_name=context.zone_name,
            action=recommendation.action,
            reason=recommendation.reason,
            score=recommendation.score,
            moisture=context.moisture,
            light=context.light,
            moisture_threshold_low=context.low,
            moisture_threshold_high=context.high,
        )

    @staticmethod
    def _summarize(zones: list[ZoneRecommendationDto]) -> tuple[str, str]:
        """Location-level action: irrigate if any zone needs water."""
        if not zones:
            return ACTION_WAIT, "Location has no zones"
        if len(zones) == 1:
            return zones[0].action, zones[0].reason

        thirsty = [z.zone_name for z in zones if z.action == ACTION_IRRIGATE]
        if thirsty:
            return (
                ACTION_IRRIGATE,
                f"{len(thirsty)} of {len(zones)} zones need water: {', '.join(thirsty)}",
            )
        return ACTION_WAIT, f"All {len(zones)} zones can wait"
