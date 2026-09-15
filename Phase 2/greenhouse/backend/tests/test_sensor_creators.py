"""Factory Method unit tests that do not need PostgreSQL."""

import pytest

from domain.sensors.creators import LightSensorCreator, MoistureSensorCreator, get_creator


def test_moisture_creator_defaults():
    sensor = MoistureSensorCreator().create_sensor()
    assert sensor.device_type == "moisture_sensor"
    assert sensor.default_config["unit"] == "vwc"
    assert "low_moisture_threshold" in sensor.default_config


def test_light_creator_defaults():
    sensor = LightSensorCreator().create_sensor()
    assert sensor.device_type == "light_sensor"
    assert sensor.default_config["unit"] == "lux"
    assert sensor.default_config["unit"] != MoistureSensorCreator().create_sensor().default_config["unit"]


def test_unknown_creator_is_rejected():
    with pytest.raises(ValueError, match="Unknown sensor type"):
        get_creator("temperature")
