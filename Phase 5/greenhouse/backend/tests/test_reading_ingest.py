"""ReadingIngest with in-memory repositories."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from application.readings.sampling import SamplingService
from application.readings.service import ReadingIngest
from domain.devices.entity import Device
from domain.sensors.errors import DeviceNotFoundError, InvalidSamplingError, SensorReadError
from fakes import InMemoryDevices, InMemoryReadings, make_sensor
from infrastructure.adapters.sensors.mqtt import MqttSensorAdapter
from infrastructure.adapters.sensors.selector import select_sensor_port


def build(*devices: Device):
    repo = InMemoryDevices(list(devices))
    readings = InMemoryReadings()
    return ReadingIngest(repo, readings, select_sensor_port), readings, repo


def test_take_reading_appends_a_row_each_time():
    sensor = make_sensor("moisture_sensor")
    ingest, readings, _ = build(sensor)

    dto = ingest.take_reading(sensor.id)
    ingest.take_reading(sensor.id)

    assert readings.count_for(sensor.id) == 2
    assert dto.device_id == sensor.id
    assert dto.unit == "vwc"
    assert dto.source == "simulation"
    assert dto.recorded_at.tzinfo is not None


def test_take_reading_uses_the_vendor_adapter_when_flagged():
    sensor = make_sensor("moisture_sensor", vendor_stub=True)
    ingest, _, _ = build(sensor)

    assert ingest.take_reading(sensor.id).source == "vendor"


def test_take_reading_missing_device():
    ingest, readings, _ = build()

    with pytest.raises(DeviceNotFoundError):
        ingest.take_reading(uuid4())
    assert readings.rows == []


def test_take_reading_on_mqtt_device_is_an_adapter_error():
    sensor = make_sensor(protocol="mqtt", family="edge")
    ingest, readings, _ = build(sensor)

    with pytest.raises(SensorReadError):
        ingest.take_reading(sensor.id)
    assert readings.rows == []


def test_take_reading_on_actuator_is_rejected():
    pump = Device(uuid4(), "water_pump", "actuator", "simulation", "Pump", {"protocol": "simulation"})
    ingest, _, _ = build(pump)

    with pytest.raises(SensorReadError):
        ingest.take_reading(pump.id)


def test_record_persists_a_translated_mqtt_reading():
    sensor = make_sensor(protocol="mqtt", family="edge")
    ingest, readings, _ = build(sensor)
    now = datetime(2026, 8, 28, 9, 0, tzinfo=timezone.utc)
    reading = MqttSensorAdapter(clock=lambda: now).translate(sensor, {"value": 0.41, "unit": "vwc"})

    dto = ingest.record(sensor.id, reading)

    assert readings.count_for(sensor.id) == 1
    assert (dto.value, dto.unit, dto.source, dto.recorded_at) == (0.41, "vwc", "mqtt", now)


def test_record_rejects_reading_of_another_device():
    sensor = make_sensor(protocol="mqtt", family="edge")
    other = make_sensor(protocol="mqtt", family="edge")
    ingest, readings, _ = build(sensor, other)
    reading = MqttSensorAdapter().translate(other, {"value": 0.3, "unit": "vwc"})

    with pytest.raises(SensorReadError):
        ingest.record(sensor.id, reading)
    assert readings.rows == []


def test_list_readings_newest_first_with_limit():
    sensor = make_sensor("light_sensor")
    ingest, _, _ = build(sensor)
    for minute in (1, 3, 2):
        ingest.take_reading(sensor.id, at=datetime(2026, 8, 28, 9, minute, tzinfo=timezone.utc))

    listed = ingest.list_readings(sensor.id, limit=2)

    assert [r.recorded_at.minute for r in listed] == [3, 2]


def test_sampling_service_updates_and_validates():
    sensor = make_sensor(interval=300, tracking=True)
    repo = InMemoryDevices([sensor])
    service = SamplingService(repo)

    dto = service.update(sensor.id, 30, False)
    assert (dto.sampling_interval_seconds, dto.tracking_enabled) == (30, False)
    assert repo.get(sensor.id).sampling_interval_seconds == 30

    assert service.update(sensor.id, 5, True).sampling_interval_seconds == 5

    with pytest.raises(InvalidSamplingError):
        service.update(sensor.id, 4, True)
    with pytest.raises(DeviceNotFoundError):
        service.update(uuid4(), 30, True)
