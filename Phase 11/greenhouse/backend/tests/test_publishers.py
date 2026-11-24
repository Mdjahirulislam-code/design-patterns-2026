"""Publishers: ingest, commands and transitions publish events and never write alerts."""

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from application.actuators.service import ActuatorStateService, ActuatorTransitionService
from application.alerts.subscribers import subscribe_alert_handlers
from application.commands.service import CommandService
from application.readings.sampler import SimulationSampler
from application.readings.service import ReadingIngest
from domain.events.bus import EventBus
from domain.events.events import ActuatorStateChanged, CommandFailed, ReadingCreated
from domain.sensors.reading import Reading
from fakes import (
    InMemoryActuatorStates,
    InMemoryAlerts,
    InMemoryCommandLog,
    InMemoryDevices,
    InMemoryExecutionLog,
    InMemoryLocations,
    InMemoryReadings,
    RecordingBus,
    SpyActuatorPort,
    make_actuator,
    make_sensor,
)
from infrastructure.adapters.actuators.factory import build_actuator_port
from infrastructure.adapters.sensors.selector import select_sensor_port

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
SRC = Path(__file__).resolve().parents[1] / "src"


# ---------------- reading.created ----------------

def test_tracked_manual_read_publishes_reading_created_with_zone_and_location():
    location, zone = uuid4(), uuid4()
    devices = InMemoryDevices()
    readings = InMemoryReadings()
    bus = RecordingBus()
    sensor = devices.place(make_sensor("moisture_sensor", zone_id=zone, location_id=location))
    ingest = ReadingIngest(devices, readings, select_sensor_port, events=bus)

    dto = ingest.take_reading(sensor.id, at=NOW)

    (event,) = bus.of(ReadingCreated)
    assert (event.device_id, event.value, event.unit, event.source, event.recorded_at) == (
        sensor.id, dto.value, "vwc", "simulation", NOW)
    assert (event.location_id, event.zone_id) == (location, zone)


def test_tracking_off_stores_the_row_and_does_not_publish():
    devices = InMemoryDevices()
    readings = InMemoryReadings()
    bus = RecordingBus()
    sensor = devices.place(make_sensor("moisture_sensor", tracking=False))
    ingest = ReadingIngest(devices, readings, select_sensor_port, events=bus)

    ingest.take_reading(sensor.id)
    ingest.record(sensor.id, Reading(sensor.id, 0.1, "vwc", "mqtt", NOW))

    assert readings.count_for(sensor.id) == 2
    assert bus.events == []


def test_unassigned_device_publishes_null_ids():
    devices = InMemoryDevices()
    bus = RecordingBus()
    sensor = devices.place(make_sensor("moisture_sensor"))
    ReadingIngest(devices, InMemoryReadings(), select_sensor_port, events=bus).take_reading(sensor.id)

    (event,) = bus.of(ReadingCreated)
    assert (event.location_id, event.zone_id) == (None, None)


def test_sampler_and_mqtt_record_use_the_same_publish():
    devices = InMemoryDevices()
    readings = InMemoryReadings()
    bus = RecordingBus()
    sensor = devices.place(make_sensor("moisture_sensor", interval=5))
    ingest = ReadingIngest(devices, readings, select_sensor_port, events=bus)

    SimulationSampler(devices, readings, ingest).run_once(NOW)              # sampler
    ingest.record(sensor.id, Reading(sensor.id, 0.3, "vwc", "mqtt", NOW))  # MQTT translation

    assert [e.source for e in bus.of(ReadingCreated)] == ["simulation", "mqtt"]


def test_low_reading_on_bench1_ends_as_alert_through_the_bus():
    locations = InMemoryLocations()
    alerts = InMemoryAlerts()
    location = locations.add_location("Lab Site A")
    bench1 = locations.add_zone(location, "Bench 1", 0.20, 0.45)
    devices = InMemoryDevices()
    sensor = devices.place(make_sensor("moisture_sensor", zone_id=bench1, location_id=location))
    bus = subscribe_alert_handlers(EventBus(), locations, alerts)
    ingest = ReadingIngest(devices, InMemoryReadings(), select_sensor_port, events=bus)

    ingest.record(sensor.id, Reading(sensor.id, 0.10, "vwc", "mqtt", NOW))

    (row,) = alerts.rows
    assert (row.event_type, row.zone_id, row.location_id) == ("threshold.crossed", bench1, location)


# ---------------- command.failed / state.changed ----------------

def command_world():
    devices = InMemoryDevices()
    states = InMemoryActuatorStates()
    bus = RecordingBus()
    pump = devices.place(make_actuator("water_pump"))  # unassigned
    states.set(pump.id, "idle", NOW)
    port = build_actuator_port(
        executions=InMemoryExecutionLog(), states=states, clock=lambda: NOW,
        adapter=SpyActuatorPort(),
    )
    service = CommandService(devices, states, port, InMemoryCommandLog(), events=bus)
    return service, states, bus, pump


def test_failed_command_publishes_command_failed_with_null_ids():
    service, states, bus, pump = command_world()
    states.set(pump.id, "running", NOW - timedelta(minutes=31))

    row = service.execute("stop_pump", pump.id)

    assert row.status == "failed"
    (event,) = bus.of(CommandFailed)
    assert (event.device_id, event.location_id, event.zone_id) == (pump.id, None, None)
    assert (event.command_type, event.message) == ("stop_pump", "Max run time exceeded")
    assert bus.of(ActuatorStateChanged) == []


def test_successful_command_publishes_state_changed():
    service, _, bus, pump = command_world()

    service.execute("start_pump", pump.id)

    (event,) = bus.of(ActuatorStateChanged)
    assert (event.previous_state, event.state) == ("idle", "running")


def test_rejected_command_publishes_nothing():
    service, _, bus, pump = command_world()

    assert service.execute("stop_pump", pump.id).status == "rejected"
    assert bus.events == []


def test_transition_to_error_publishes_and_is_stored_as_critical():
    devices = InMemoryDevices()
    states = InMemoryActuatorStates()
    alerts = InMemoryAlerts()
    pump = devices.place(make_actuator("water_pump"))
    states.set(pump.id, "idle", NOW)
    bus = subscribe_alert_handlers(EventBus(), InMemoryLocations(), alerts)

    ActuatorTransitionService(devices, states, events=bus).transition(pump.id, "error")

    (row,) = alerts.rows
    assert (row.event_type, row.severity, row.message) == (
        "state.changed", "critical", "Actuator entered error")
    assert ActuatorTransitionService is ActuatorStateService


# ---------------- publishers do not know the alerts table ----------------

def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{a.name}" for a in node.names)
        elif isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
    return names


def test_publishers_do_not_import_alert_repository():
    for module in (
        "application/readings/service.py",
        "application/commands/service.py",
        "application/actuators/service.py",
    ):
        imports = _imports(SRC / module)
        assert not any("alert" in name.lower() for name in imports), (module, imports)
