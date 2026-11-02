"""LocationOverviewFacade: one entry point for the dashboard overview.

The facade only coordinates existing subsystems and builds the read model:

  locations + zones      -> LocationRepository.get_with_zones        (Phase 4)
  assigned devices       -> DeviceRepository.list_assigned_to_location (one query)
  newest readings        -> ReadingRepository.latest_for_devices      (one query)
  saved strategy key     -> AutomationRuleRepository.get              (Phase 6)
  last recommendation    -> AutomationService.evaluate                (Phase 6)
  actuator states        -> ActuatorStateRepository.get_many          (Phase 8, one query)

It does not decide irrigation itself (Strategy does that inside evaluate), does
not translate sensor payloads (Adapter) and does not write anything.
"""

from typing import Protocol
from uuid import UUID

from application.overview.dto import (
    DeviceCountsDto,
    LastRecommendationDto,
    LocationOverviewDto,
    OverviewDeviceDto,
    OverviewLocationDto,
    OverviewReadingDto,
    OverviewZoneDto,
)
from domain.actuators.state import INITIAL_STATE, allowed_commands_for
from domain.automation.rule import StrategyRule
from domain.devices.entity import Device
from domain.locations.entity import LocationSummary, ZoneThresholds
from domain.locations.errors import LocationNotFoundError
from domain.sensors.reading import Reading


class OverviewLocations(Protocol):
    def get_with_zones(
        self, location_id: UUID
    ) -> tuple[LocationSummary, list[ZoneThresholds]] | None: ...


class AssignedDevices(Protocol):
    def list_assigned_to_location(self, location_id: UUID) -> list[Device]: ...


class NewestReadings(Protocol):
    def latest_for_devices(self, device_ids: list[UUID]) -> dict[UUID, Reading]: ...


class SavedStrategies(Protocol):
    def get(self, location_id: UUID) -> StrategyRule | None: ...


class Recommendation(Protocol):
    action: str
    reason: str


class LocationEvaluator(Protocol):
    def evaluate(self, location_id: UUID) -> Recommendation: ...


class ActuatorStates(Protocol):
    def get_many(self, device_ids: list[UUID]) -> dict[UUID, str]: ...


class _NoStates:
    """Used when no state store is given (keeps Phase 7 callers working)."""

    def get_many(self, device_ids: list[UUID]) -> dict[UUID, str]:
        return {}


class LocationOverviewFacade:
    def __init__(
        self,
        locations: OverviewLocations,
        devices: AssignedDevices,
        readings: NewestReadings,
        rules: SavedStrategies,
        automation: LocationEvaluator,
        states: ActuatorStates | None = None,
    ) -> None:
        self._locations = locations
        self._devices = devices
        self._readings = readings
        self._rules = rules
        self._automation = automation
        self._states = states or _NoStates()

    def get_overview(self, location_id: UUID) -> LocationOverviewDto:
        # 1. location + every zone (missing location -> 404 in the API)
        loaded = self._locations.get_with_zones(location_id)
        if loaded is None:
            raise LocationNotFoundError(f"Location {location_id} not found")
        location, zones = loaded

        # 2. assigned devices: one query for the location; keep only devices
        #    whose zone really belongs to this location
        zone_ids = {zone.zone_id for zone in zones}
        devices = [
            device
            for device in self._devices.list_assigned_to_location(location_id)
            if device.zone_id in zone_ids
        ]

        # 3. newest reading of all those devices: one query, not one per device
        latest = self._readings.latest_for_devices([device.id for device in devices])

        # Phase 8: lifecycle state of the assigned actuators, one query
        actuator_ids = [device.id for device in devices if device.role == "actuator"]
        states = self._states.get_many(actuator_ids) if actuator_ids else {}

        # 4. saved strategy, and 5. evaluate only when a key is saved.
        #    evaluate runs the saved Strategy; the facade never calls decide().
        rule = self._rules.get(location_id)
        last_recommendation = None
        if rule is not None:
            result = self._automation.evaluate(location_id)
            last_recommendation = LastRecommendationDto(
                action=result.action, reason=result.reason
            )

        return LocationOverviewDto(
            location=OverviewLocationDto(id=location.id, name=location.name),
            device_counts=DeviceCountsDto(
                sensor=sum(1 for device in devices if device.role == "sensor"),
                actuator=sum(1 for device in devices if device.role == "actuator"),
            ),
            zones=[self._zone(zone, devices, latest, states) for zone in zones],
            strategy_key=rule.strategy_key if rule else None,
            last_recommendation=last_recommendation,
        )

    @staticmethod
    def _zone(
        zone: ZoneThresholds,
        devices: list[Device],
        latest: dict[UUID, Reading],
        states: dict[UUID, str],
    ) -> OverviewZoneDto:
        in_zone = [device for device in devices if device.zone_id == zone.zone_id]

        return OverviewZoneDto(
            id=zone.zone_id,
            name=zone.name,
            moisture_threshold_low=zone.moisture_threshold_low,
            moisture_threshold_high=zone.moisture_threshold_high,
            devices=[
                LocationOverviewFacade._device(device, states)
                for device in in_zone
            ],
            latest_readings=[
                OverviewReadingDto(
                    device_id=device.id,
                    value=latest[device.id].value,
                    unit=latest[device.id].unit,
                    recorded_at=latest[device.id].recorded_at,
                    # sampling settings come from the device, not the reading
                    tracking_enabled=device.tracking_enabled,
                    sampling_interval_seconds=device.sampling_interval_seconds,
                )
                for device in in_zone
                if device.id in latest
            ],
        )

    @staticmethod
    def _device(device: Device, states: dict[UUID, str]) -> OverviewDeviceDto:
        state = None
        commands: list[str] = []
        if device.role == "actuator":
            state = states.get(device.id, INITIAL_STATE)
            commands = allowed_commands_for(state)

        return OverviewDeviceDto(
            id=device.id,
            device_type=device.device_type,
            role=device.role,
            display_name=device.display_name,
            state=state,
            allowed_commands=commands,
        )
