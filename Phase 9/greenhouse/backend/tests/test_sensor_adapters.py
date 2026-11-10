"""Adapter unit tests: translation and generation. No HTTP, no database, no broker."""

import socket
from datetime import datetime, timezone

import pytest

from domain.sensors.errors import SensorReadError
from domain.sensors.ports import SensorPort
from fakes import make_sensor
from infrastructure.adapters.sensors.mqtt import MqttSensorAdapter
from infrastructure.adapters.sensors.selector import select_sensor_port
from infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter


class FixedVendorClient:
    """Returns one canned vendor payload and remembers how it was called."""

    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[tuple[str, str]] = []

    def poll(self, probe_serial: str, channel: str) -> dict:
        self.calls.append((probe_serial, channel))
        return self.payload


# ---------------- simulation ----------------

def test_simulation_adapter_value_in_range():
    adapter = SimulationSensorAdapter()
    moisture = make_sensor("moisture_sensor")
    light = make_sensor("light_sensor")

    for _ in range(300):
        m = adapter.read(moisture)
        assert 0.2 <= m.value <= 0.6
        assert m.unit == "vwc"
        assert m.source == "simulation"

        lux = adapter.read(light)
        assert 200 <= lux.value <= 2000
        assert lux.unit == "lux"
        assert lux.source == "simulation"


def test_simulation_adapter_returns_normalized_reading():
    device = make_sensor("moisture_sensor")
    reading = SimulationSensorAdapter().read(device)

    assert reading.device_id == device.id
    assert reading.recorded_at.tzinfo is not None


def test_simulation_adapter_rejects_unknown_device_type():
    with pytest.raises(SensorReadError):
        SimulationSensorAdapter().read(make_sensor("water_pump"))


# ---------------- vendor stub ----------------

def test_vendor_adapter_normalizes_raw_payload():
    device = make_sensor("moisture_sensor", vendor_stub=True)
    client = FixedVendorClient(
        {
            "probeSerial": str(device.id),
            "statusCode": 0,
            "statusText": "OK",
            "tsEpochMs": 1_787_994_000_000,
            "measurement": {"qty": "SOIL_H2O", "val": 41.0, "uom": "PCT"},
        }
    )

    reading = VendorStubSensorAdapter(client).read(device)

    assert client.calls == [(str(device.id), "SOIL_H2O")]
    assert reading.device_id == device.id
    assert reading.value == pytest.approx(0.41)  # percent -> vwc fraction
    assert reading.unit == "vwc"
    assert reading.source == "vendor"
    assert reading.recorded_at == datetime.fromtimestamp(1_787_994_000, tz=timezone.utc)


def test_vendor_adapter_converts_kilolux_to_lux():
    device = make_sensor("light_sensor", vendor_stub=True)
    client = FixedVendorClient(
        {
            "statusCode": 0,
            "tsEpochMs": 1_787_994_000_000,
            "measurement": {"qty": "ILLUM", "val": 1.25, "uom": "KLX"},
        }
    )

    reading = VendorStubSensorAdapter(client).read(device)

    assert reading.value == pytest.approx(1250.0)
    assert reading.unit == "lux"


def test_vendor_adapter_turns_vendor_status_into_domain_error():
    device = make_sensor("moisture_sensor", vendor_stub=True)
    client = FixedVendorClient({"statusCode": 7, "statusText": "PROBE_OFFLINE"})

    with pytest.raises(SensorReadError, match="PROBE_OFFLINE"):
        VendorStubSensorAdapter(client).read(device)


def test_vendor_adapter_rejects_malformed_payload():
    device = make_sensor("moisture_sensor", vendor_stub=True)
    client = FixedVendorClient({"statusCode": 0, "measurement": {"val": "wet"}})

    with pytest.raises(SensorReadError):
        VendorStubSensorAdapter(client).read(device)


def test_vendor_stub_default_client_stays_in_simulation_ranges():
    reading = VendorStubSensorAdapter().read(make_sensor("moisture_sensor", vendor_stub=True))
    assert 0.2 <= reading.value <= 0.6
    assert reading.source == "vendor"


# ---------------- mqtt ----------------

def test_mqtt_adapter_translates_payload(monkeypatch):
    def no_sockets(*args, **kwargs):
        raise AssertionError("MQTT translation must not open a socket")

    monkeypatch.setattr(socket, "socket", no_sockets)
    monkeypatch.setattr(socket, "create_connection", no_sockets)

    device = make_sensor("moisture_sensor", protocol="mqtt", family="edge")
    now = datetime(2026, 8, 28, 9, 0, tzinfo=timezone.utc)

    reading = MqttSensorAdapter(clock=lambda: now).translate(
        device, {"value": 0.41, "unit": "vwc"}
    )

    assert reading.device_id == device.id
    assert reading.value == 0.41
    assert reading.unit == "vwc"
    assert reading.source == "mqtt"
    assert reading.recorded_at == now


def test_mqtt_adapter_rejects_bad_payloads():
    device = make_sensor("moisture_sensor", protocol="mqtt", family="edge")
    adapter = MqttSensorAdapter()

    for payload in ({}, {"value": "0.41", "unit": "vwc"}, {"value": True, "unit": "vwc"},
                    {"value": float("nan"), "unit": "vwc"}, {"value": 0.4}):
        with pytest.raises(SensorReadError):
            adapter.translate(device, payload)


# ---------------- selector ----------------

def test_selector_returns_ports_with_different_sources():
    simulated = make_sensor("moisture_sensor")
    vendor = make_sensor("moisture_sensor", vendor_stub=True)

    sim_port = select_sensor_port(simulated)
    vendor_port = select_sensor_port(vendor)

    assert isinstance(sim_port, SensorPort)
    assert isinstance(vendor_port, SensorPort)
    assert sim_port.read(simulated).source == "simulation"
    assert vendor_port.read(vendor).source == "vendor"


def test_selector_understands_phase_3_protocol_names():
    legacy = make_sensor("light_sensor", protocol="sim")
    assert select_sensor_port(legacy).read(legacy).source == "simulation"


def test_selector_has_no_pull_adapter_for_mqtt():
    with pytest.raises(SensorReadError, match="MQTT"):
        select_sensor_port(make_sensor(protocol="mqtt", family="edge"))
