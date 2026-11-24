"""EventBus: the subject of the Observer pattern (in-process, synchronous).

Publishers call `publish(event)` and never know who listens. Subscribers
register with `subscribe(EventClass, handler)`. Handlers of one event class run
in subscription order. There is no unsubscribe in this phase.

One failing handler must not stop the others: its exception is logged and the
remaining handlers still run (so a broken alert writer cannot block metrics or
the Phase 12 WebSocket).
"""

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any, Protocol

logger = logging.getLogger(__name__)

Handler = Callable[[Any], None]


class EventPublisher(Protocol):
    """What a publisher needs: only `publish`."""

    def publish(self, event: object) -> None: ...


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = defaultdict(list)
        self.errors: list[tuple[object, Exception]] = []

    def subscribe(self, event_type: type, handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: object) -> None:
        for handler in list(self._handlers.get(type(event), ())):
            try:
                handler(event)
            except Exception as error:  # noqa: BLE001 - isolate subscribers
                self.errors.append((event, error))
                logger.exception(
                    "Subscriber %r failed on %s", handler, getattr(event, "event_type", event)
                )

    def subscriber_count(self, event_type: type) -> int:
        return len(self._handlers.get(event_type, ()))


class NullEventBus:
    """Default for services built without a bus (old tests, scripts). Drops events."""

    def publish(self, event: object) -> None:
        return None
