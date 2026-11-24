"""Wires the SimulationSampler to real repositories and runs it in the background.

The sampler itself (application/readings/sampler.py) knows nothing about
asyncio, sessions or sleeping. Tests call `run_once(now)` directly.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from application.readings.sampler import SimulationSampler
from application.readings.service import ReadingIngest
from infrastructure.adapters.sensors.selector import select_sensor_port
from domain.events.bus import EventPublisher
from infrastructure.db import SessionLocal
from infrastructure.events import build_event_bus
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository
from infrastructure.settings import settings

logger = logging.getLogger(__name__)

ERROR_BACKOFF_SECONDS = 15.0


def build_reading_ingest(session: Session, events: EventPublisher | None = None) -> ReadingIngest:
    """The one ingest used by POST /read, the sampler and (later) MQTT.

    Phase 11: it gets the event bus, so every path publishes reading.created
    the same way.
    """
    return ReadingIngest(
        devices=DeviceRepository(session),
        readings=ReadingRepository(session),
        select_port=select_sensor_port,
        events=events if events is not None else build_event_bus(session),
    )


def build_sampler(session: Session) -> SimulationSampler:
    return SimulationSampler(
        devices=DeviceRepository(session),
        readings=ReadingRepository(session),
        ingest=build_reading_ingest(session),
    )


def run_sampler_tick() -> int:
    """One tick with its own short-lived database session."""
    session = SessionLocal()
    try:
        return build_sampler(session).run_once(datetime.now(timezone.utc))
    finally:
        session.close()


async def sampler_loop() -> None:
    """Runs until cancelled by the app lifespan."""
    logger.info("Simulation sampler started (tick %.1fs)", settings.sampler_tick_seconds)

    while True:
        delay = settings.sampler_tick_seconds
        try:
            # blocking database work runs in a worker thread, not on the event loop
            await asyncio.to_thread(run_sampler_tick)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - the loop must survive a failed tick
            logger.warning("Simulation sampler tick failed: %s", exc)
            delay = ERROR_BACKOFF_SECONDS

        await asyncio.sleep(delay)
