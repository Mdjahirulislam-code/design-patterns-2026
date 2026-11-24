"""Composition root of the Observer wiring (Phase 11).

`build_event_bus(session)` creates one EventBus, subscribes the two alert
subscribers to it, and is handed to every publisher built for the same request
(or the same sampler tick). The subscribers use the same database session.

Phase 12: subscribe the dashboard WebSocket to this bus here (for example to
AlertCreated and ReadingCreated) instead of writing a second pub/sub system.
"""

from sqlalchemy.orm import Session

from application.alerts.subscribers import subscribe_alert_handlers
from domain.events.bus import EventBus
from infrastructure.persistence.alert_repository import AlertRepository
from infrastructure.persistence.location_repository import LocationRepository


def build_event_bus(session: Session) -> EventBus:
    return subscribe_alert_handlers(
        EventBus(),
        zones=LocationRepository(session),
        alerts=AlertRepository(session),
    )
