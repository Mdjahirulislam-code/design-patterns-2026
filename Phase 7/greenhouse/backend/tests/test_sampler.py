"""SimulationSampler driven by a fake clock. No sleeping, no HTTP, no broker."""

from datetime import datetime, timedelta, timezone

from application.readings.sampler import SimulationSampler
from application.readings.sampling import SamplingService
from application.readings.service import ReadingIngest
from fakes import InMemoryDevices, InMemoryReadings, make_sensor
from infrastructure.adapters.sensors.selector import select_sensor_port

T0 = datetime(2026, 8, 28, 9, 0, 0, tzinfo=timezone.utc)


def build(*devices):
    repo = InMemoryDevices(list(devices))
    readings = InMemoryReadings()
    ingest = ReadingIngest(repo, readings, select_sensor_port)
    return SimulationSampler(repo, readings, ingest), readings, repo


def test_sampler_respects_interval_and_tracking():
    enabled = make_sensor("moisture_sensor", interval=60, tracking=True)
    disabled = make_sensor("moisture_sensor", interval=60, tracking=False)
    mqtt = make_sensor("moisture_sensor", protocol="mqtt", family="edge", interval=60)
    sampler, readings, _ = build(enabled, disabled, mqtt)

    # no previous row counts as elapsed
    assert sampler.run_once(T0) == 1
    assert readings.count_for(enabled.id) == 1

    # second call inside the interval: nothing new
    assert sampler.run_once(T0 + timedelta(seconds=59)) == 0
    assert readings.count_for(enabled.id) == 1

    # interval has elapsed: one more row
    assert sampler.run_once(T0 + timedelta(seconds=60)) == 1
    assert readings.count_for(enabled.id) == 2

    # disabled and MQTT devices never gain sampler rows
    assert readings.count_for(disabled.id) == 0
    assert readings.count_for(mqtt.id) == 0


def test_sampler_rows_use_the_tick_time_and_simulation_source():
    sensor = make_sensor("light_sensor", interval=10)
    sampler, readings, _ = build(sensor)

    sampler.run_once(T0)

    row = readings.latest_for_device(sensor.id)
    assert row.recorded_at == T0
    assert row.source == "simulation"
    assert 200 <= row.value <= 2000


def test_each_device_follows_its_own_interval():
    fast = make_sensor("moisture_sensor", interval=5)
    slow = make_sensor("light_sensor", interval=300)
    sampler, readings, _ = build(fast, slow)

    for seconds in range(0, 21, 5):  # ticks at 0, 5, 10, 15, 20
        sampler.run_once(T0 + timedelta(seconds=seconds))

    assert readings.count_for(fast.id) == 5
    assert readings.count_for(slow.id) == 1


def test_manual_read_counts_as_the_last_reading():
    sensor = make_sensor("moisture_sensor", interval=60)
    repo = InMemoryDevices([sensor])
    readings = InMemoryReadings()
    ingest = ReadingIngest(repo, readings, select_sensor_port)
    sampler = SimulationSampler(repo, readings, ingest)

    ingest.take_reading(sensor.id, at=T0)  # "Read now"

    assert sampler.run_once(T0 + timedelta(seconds=30)) == 0
    assert sampler.run_once(T0 + timedelta(seconds=61)) == 1


def test_turning_tracking_off_and_on_again():
    sensor = make_sensor("moisture_sensor", interval=10)
    sampler, readings, repo = build(sensor)
    sampling = SamplingService(repo)

    sampler.run_once(T0)
    sampling.update(sensor.id, 10, False)
    assert sampler.run_once(T0 + timedelta(seconds=100)) == 0

    sampling.update(sensor.id, 10, True)
    assert sampler.run_once(T0 + timedelta(seconds=101)) == 1
    assert readings.count_for(sensor.id) == 2


def test_shorter_interval_inserts_sooner():
    sensor = make_sensor("moisture_sensor", interval=300)
    sampler, readings, repo = build(sensor)

    sampler.run_once(T0)
    assert sampler.run_once(T0 + timedelta(seconds=20)) == 0

    SamplingService(repo).update(sensor.id, 15, True)
    assert sampler.run_once(T0 + timedelta(seconds=20)) == 1


def test_sampler_skips_vendor_stub_and_unreadable_devices():
    vendor = make_sensor("moisture_sensor", vendor_stub=True, interval=5)
    unknown = make_sensor("co2_sensor", interval=5)  # simulation cannot generate this
    good = make_sensor("moisture_sensor", interval=5)
    sampler, readings, _ = build(vendor, unknown, good)

    assert sampler.run_once(T0) == 1
    assert readings.count_for(good.id) == 1
    assert readings.count_for(vendor.id) == 0
    assert readings.count_for(unknown.id) == 0
