"""Tests for Plant Monitor BLE binary sensors."""

import pytest

pytest.importorskip("homeassistant")

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory

from custom_components.plant_monitor_ble.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
    binary_sensor_update_to_bluetooth_data_update,
)
from custom_components.plant_monitor_ble.parser import parse_frame

from .conftest import ADDRESS, FRAME


def _with_status(status: int) -> bytes:
    changed = bytearray(FRAME)
    changed[2:4] = status.to_bytes(2, "little")
    return bytes(changed)


def test_binary_sensor_metadata_and_defaults() -> None:
    descriptions = {
        description.key: description for description in BINARY_SENSOR_DESCRIPTIONS
    }
    assert set(descriptions) == {
        "calibration_invalid",
        "battery_low",
        "bottom_saturation",
        "middle_saturation",
        "top_saturation",
        "tsc_acquisition_fault",
        "environmental_sensor_fault",
        "battery_measurement_fault",
        "i2c_fault",
        "ble_fault",
        "oscillator_configuration_fault",
    }
    for description in descriptions.values():
        assert description.device_class is BinarySensorDeviceClass.PROBLEM
        assert description.entity_category is EntityCategory.DIAGNOSTIC
    assert {
        key
        for key, description in descriptions.items()
        if description.entity_registry_enabled_default
    } == {"calibration_invalid", "battery_low", "environmental_sensor_fault"}


def test_status_flags_update_binary_sensors() -> None:
    status = sum(1 << bit for bit in range(1, 15))
    update = parse_frame(_with_status(status), address=ADDRESS)
    assert update is not None
    data = binary_sensor_update_to_bluetooth_data_update(update)
    values = {key.key: value for key, value in data.entity_data.items()}
    assert all(values.values())

    update = parse_frame(_with_status(0), address=ADDRESS)
    assert update is not None
    data = binary_sensor_update_to_bluetooth_data_update(update)
    assert not any(data.entity_data.values())


def test_aggregate_binary_sensor_flags() -> None:
    for bit in (6, 7):
        update = parse_frame(_with_status(1 << bit), address=ADDRESS)
        assert update is not None
        data = binary_sensor_update_to_bluetooth_data_update(update)
        values = {key.key: value for key, value in data.entity_data.items()}
        assert values["environmental_sensor_fault"]
    for bit in (13, 14):
        update = parse_frame(_with_status(1 << bit), address=ADDRESS)
        assert update is not None
        data = binary_sensor_update_to_bluetooth_data_update(update)
        values = {key.key: value for key, value in data.entity_data.items()}
        assert values["oscillator_configuration_fault"]
