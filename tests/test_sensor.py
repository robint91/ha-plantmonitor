"""Tests for Plant Monitor BLE sensor entities."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

pytest.importorskip("homeassistant")

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.plant_monitor_ble.parser import parse_frame
from custom_components.plant_monitor_ble.sensor import (
    SENSOR_DESCRIPTIONS,
    sensor_update_to_bluetooth_data_update,
)

from .conftest import ADDRESS, FRAME


async def _setup_with_update(
    hass: HomeAssistant, entry: MockConfigEntry, frame: bytes = FRAME
):
    with patch(
        "custom_components.plant_monitor_ble.coordinator."
        "PlantMonitorBluetoothCoordinator.async_start",
        return_value=lambda: None,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    update = parse_frame(frame, address=ADDRESS, rssi=-67)
    assert update is not None
    entry.runtime_data.async_set_updated_data(update)
    await hass.async_block_till_done()
    return update


async def test_all_entities_and_device_registry(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    await _setup_with_update(hass, mock_config_entry)
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert len(entries) == 25
    assert sum(entry.disabled_by is None for entry in entries) == 9
    assert sum(entry.disabled_by is not None for entry in entries) == 16

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(
        connections={(CONNECTION_BLUETOOTH, ADDRESS)}
    )
    assert device is not None
    assert mock_config_entry.entry_id in device.config_entries


def test_sensor_description_metadata() -> None:
    descriptions = {description.key: description for description in SENSOR_DESCRIPTIONS}
    for key in ("bottom_moisture", "middle_moisture", "top_moisture"):
        description = descriptions[key]
        assert description.device_class is SensorDeviceClass.MOISTURE
        assert description.native_unit_of_measurement == PERCENTAGE
        assert description.state_class is SensorStateClass.MEASUREMENT
        assert description.suggested_display_precision == 2
    temperature = descriptions["air_temperature"]
    assert temperature.device_class is SensorDeviceClass.TEMPERATURE
    assert temperature.native_unit_of_measurement is UnitOfTemperature.CELSIUS
    assert temperature.suggested_display_precision == 2
    humidity = descriptions["relative_humidity"]
    assert humidity.device_class is SensorDeviceClass.HUMIDITY
    assert humidity.native_unit_of_measurement == PERCENTAGE
    assert humidity.suggested_display_precision == 2
    battery = descriptions["battery_voltage"]
    assert battery.device_class is SensorDeviceClass.VOLTAGE
    assert battery.native_unit_of_measurement is UnitOfElectricPotential.MILLIVOLT
    assert battery.entity_category is EntityCategory.DIAGNOSTIC
    assert battery.entity_registry_enabled_default is True
    for description in SENSOR_DESCRIPTIONS[6:]:
        assert description.entity_category is EntityCategory.DIAGNOSTIC
        assert description.entity_registry_enabled_default is False


def test_sensor_values_and_unknown_sentinels() -> None:
    changed = bytearray(FRAME)
    for offset in (6, 8, 10, 12, 14, 16, 18, 22):
        changed[offset : offset + 2] = b"\xff\xff"
    changed[20:22] = b"\x00\x80"
    update = parse_frame(bytes(changed), address=ADDRESS)
    assert update is not None
    data = sensor_update_to_bluetooth_data_update(update)
    values = {key.key: value for key, value in data.entity_data.items()}
    for key in (
        "bottom_moisture",
        "middle_moisture",
        "top_moisture",
        "air_temperature",
        "relative_humidity",
        "battery_voltage",
        "bottom_filtered_count",
        "middle_filtered_count",
        "top_filtered_count",
    ):
        assert values[key] is None
    assert values["bottom_moisture"] != 0


async def test_native_units_and_stale_availability(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, service_info_factory
) -> None:
    await _setup_with_update(hass, mock_config_entry)
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_config_entry.entry_id)
    by_key = {entry.unique_id.rsplit("-", 1)[-1]: entry for entry in entries}

    moisture = hass.states.get(by_key["bottom_moisture"].entity_id)
    assert moisture is not None
    assert moisture.state == "12.34"
    assert moisture.attributes[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert moisture.attributes["device_class"] == SensorDeviceClass.MOISTURE
    assert moisture.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert moisture.state != "unavailable"

    temperature = hass.states.get(by_key["air_temperature"].entity_id)
    assert temperature is not None
    assert temperature.attributes[ATTR_UNIT_OF_MEASUREMENT] == "°C"
    battery = hass.states.get(by_key["battery_voltage"].entity_id)
    assert battery is not None
    assert battery.attributes[ATTR_UNIT_OF_MEASUREMENT] == "mV"

    with patch(
        "custom_components.plant_monitor_ble.coordinator.async_call_later",
        return_value=lambda: None,
    ) as schedule_stale:
        update = mock_config_entry.runtime_data.process_advertisement(
            service_info_factory()
        )
        assert update is not None
        mock_config_entry.runtime_data.async_set_updated_data(update)
        assert schedule_stale.call_args.args[1] == 90
        stale_callback = schedule_stale.call_args.args[2]
        stale_callback(datetime.now(timezone.utc))
        await hass.async_block_till_done()
    moisture = hass.states.get(by_key["bottom_moisture"].entity_id)
    assert moisture is not None
    assert moisture.state == "unavailable"
