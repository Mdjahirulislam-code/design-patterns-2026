"""EventBus: subscribe, publish, order and isolation of a failing subscriber."""

from dataclasses import dataclass

from domain.events.bus import EventBus, NullEventBus


@dataclass
class Ping:
    n: int


@dataclass
class Pong:
    n: int


def test_handlers_run_in_subscription_order():
    bus = EventBus()
    calls = []
    bus.subscribe(Ping, lambda e: calls.append(("first", e.n)))
    bus.subscribe(Ping, lambda e: calls.append(("second", e.n)))

    bus.publish(Ping(1))

    assert calls == [("first", 1), ("second", 1)]


def test_only_handlers_of_that_event_class_run():
    bus = EventBus()
    calls = []
    bus.subscribe(Ping, lambda e: calls.append("ping"))
    bus.subscribe(Pong, lambda e: calls.append("pong"))

    bus.publish(Pong(1))

    assert calls == ["pong"]


def test_event_without_subscribers_is_fine():
    EventBus().publish(Ping(1))
    NullEventBus().publish(Ping(1))


def test_failing_subscriber_does_not_stop_the_others():
    bus = EventBus()
    calls = []

    def broken(event):
        raise RuntimeError("alert writer down")

    bus.subscribe(Ping, broken)
    bus.subscribe(Ping, lambda e: calls.append("metrics"))

    bus.publish(Ping(1))

    assert calls == ["metrics"]
    assert len(bus.errors) == 1
    assert str(bus.errors[0][1]) == "alert writer down"


def test_a_handler_may_publish_another_event():
    bus = EventBus()
    calls = []
    bus.subscribe(Ping, lambda e: bus.publish(Pong(e.n + 1)))
    bus.subscribe(Pong, lambda e: calls.append(e.n))

    bus.publish(Ping(1))

    assert calls == [2]
