"""Concrete observers. They react to events; the publishers never call them directly.

MoistureThresholdSubscriber   ReadingCreated -> ThresholdCrossed (moisture strictly below zone low)
AlertPersistenceSubscriber    ThresholdCrossed / CommandFailed / ActuatorStateChanged(error)
                              -> one active row in `alerts`, then AlertCreated
"""

from typing import Protocol
from uuid import UUID

from domain.actuators.state import ERROR
from domain.alerts import SEVERITY_CRITICAL, SEVERITY_WARNING, Alert
from domain.events.bus import EventBus, EventPublisher
from domain.events.events import (
    ActuatorStateChanged,
    AlertCreated,
    CommandFailed,
    ReadingCreated,
    ThresholdCrossed,
)
from domain.locations.entity import ZoneThresholds

MOISTURE_UNIT = "vwc"
THRESHOLD_MESSAGE = "Moisture below zone low"
ERROR_STATE_MESSAGE = "Actuator entered error"


class ZoneLookup(Protocol):
    def get_zone_thresholds(self, zone_id: UUID) -> ZoneThresholds | None: ...


class AlertWriter(Protocol):
    def insert(
        self,
        *,
        location_id: UUID | None,
        zone_id: UUID | None,
        device_id: UUID | None,
        severity: str,
        message: str,
        event_type: str,
    ) -> Alert: ...


class MoistureThresholdSubscriber:
    def __init__(self, zones: ZoneLookup, bus: EventPublisher) -> None:
        self._zones = zones
        self._bus = bus

    def on_reading(self, event: ReadingCreated) -> None:
        if event.unit != MOISTURE_UNIT or event.zone_id is None:
            return  # only moisture, and only for a device that sits in a zone

        zone = self._zones.get_zone_thresholds(event.zone_id)
        if zone is None or not event.value < zone.moisture_threshold_low:
            return

        self._bus.publish(
            ThresholdCrossed(
                device_id=event.device_id,
                location_id=event.location_id,
                zone_id=event.zone_id,
                moisture=event.value,
                threshold_low=zone.moisture_threshold_low,
                recorded_at=event.recorded_at,
            )
        )


class AlertPersistenceSubscriber:
    def __init__(self, alerts: AlertWriter, bus: EventPublisher) -> None:
        self._alerts = alerts
        self._bus = bus

    def on_threshold(self, event: ThresholdCrossed) -> None:
        self._store(event, SEVERITY_WARNING, THRESHOLD_MESSAGE)

    def on_command(self, event: CommandFailed) -> None:
        self._store(event, SEVERITY_WARNING, event.message)

    def on_state(self, event: ActuatorStateChanged) -> None:
        if event.state == ERROR:
            self._store(event, SEVERITY_CRITICAL, ERROR_STATE_MESSAGE)

    def _store(self, event, severity: str, message: str) -> None:
        alert = self._alerts.insert(
            location_id=event.location_id,
            zone_id=event.zone_id,
            device_id=event.device_id,
            severity=severity,
            message=message,
            event_type=event.event_type,
        )
        # Phase 12 subscribes the dashboard WebSocket to this event.
        self._bus.publish(
            AlertCreated(
                alert_id=alert.id,
                device_id=alert.device_id,
                location_id=alert.location_id,
                zone_id=alert.zone_id,
                severity=alert.severity,
                message=alert.message,
                alert_event_type=alert.event_type,
                created_at=alert.created_at,
            )
        )


def subscribe_alert_handlers(bus: EventBus, zones: ZoneLookup, alerts: AlertWriter) -> EventBus:
    """Register both subscribers on a bus. Used by the composition root and tests."""
    threshold = MoistureThresholdSubscriber(zones, bus)
    persistence = AlertPersistenceSubscriber(alerts, bus)

    bus.subscribe(ReadingCreated, threshold.on_reading)
    bus.subscribe(ThresholdCrossed, persistence.on_threshold)
    bus.subscribe(CommandFailed, persistence.on_command)
    bus.subscribe(ActuatorStateChanged, persistence.on_state)
    return bus
