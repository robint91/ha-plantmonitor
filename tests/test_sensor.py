"""Tests for Plant Monitor BLE sensor entities."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

pytest.importorskip("homeassistant")

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    LIGHT_LUX,
    PERCENTAGE,
    EntityCategory,
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

from .conftest import ADDRESS, CALIBRATION, FRAME

RAW_COUNT_KEYS = ("bottom_tsc_count", "middle_tsc_count", "top_tsc_count")
MOISTURE_KEYS = ("bottom_moisture", "middle_moisture", "top_moisture")


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
    assert len(entries) == 12
    assert sum(entry.disabled_by is None for entry in entries) == 9
    assert sum(entry.disabled_by is not None for entry in entries) == 3
    unique_ids = {entry.unique_id for entry in entries}
    for key in (*RAW_COUNT_KEYS, *MOISTURE_KEYS):
        assert f"{ADDRESS}-{key}" in unique_ids
    assert not any("_tsc_1nf" in unique_id for unique_id in unique_ids)
    assert not any("_tsc_11nf" in unique_id for unique_id in unique_ids)
    assert not any("_tsc_48nf" in unique_id for unique_id in unique_ids)
    assert not any("battery" in unique_id for unique_id in unique_ids)

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(
        connections={(CONNECTION_BLUETOOTH, ADDRESS)}
    )
    assert device is not None
    assert mock_config_entry.entry_id in device.config_entries


def test_sensor_description_metadata() -> None:
    descriptions = {description.key: description for description in SENSOR_DESCRIPTIONS}
    temperature = descriptions["air_temperature"]
    assert temperature.device_class is SensorDeviceClass.TEMPERATURE
    assert temperature.native_unit_of_measurement is UnitOfTemperature.CELSIUS
    assert temperature.suggested_display_precision == 2
    humidity = descriptions["relative_humidity"]
    assert humidity.device_class is SensorDeviceClass.HUMIDITY
    assert humidity.native_unit_of_measurement == PERCENTAGE
    assert humidity.suggested_display_precision == 2
    illuminance = descriptions["illuminance"]
    assert illuminance.device_class is SensorDeviceClass.ILLUMINANCE
    assert illuminance.native_unit_of_measurement == LIGHT_LUX
    assert illuminance.suggested_display_precision == 2
    for key in RAW_COUNT_KEYS:
        description = descriptions[key]
        assert description.state_class is SensorStateClass.MEASUREMENT
        assert description.entity_category is EntityCategory.DIAGNOSTIC
        assert description.entity_registry_enabled_default is True
        assert description.device_class is None
        assert description.native_unit_of_measurement is None
    for key in MOISTURE_KEYS:
        description = descriptions[key]
        assert description.device_class is SensorDeviceClass.MOISTURE
        assert description.native_unit_of_measurement == PERCENTAGE
        assert description.state_class is SensorStateClass.MEASUREMENT
        assert description.entity_registry_enabled_default is True


def test_sensor_values_and_unknown_sentinels() -> None:
    changed = bytearray(FRAME)
    changed[2:8] = b"\xff" * 6
    changed[8:10] = b"\x00\x80"
    changed[10:12] = b"\xff\xff"
    changed[12:15] = b"\xff\xff\xff"
    update = parse_frame(bytes(changed), address=ADDRESS)
    assert update is not None
    data = sensor_update_to_bluetooth_data_update(update, CALIBRATION)
    values = {key.key: value for key, value in data.entity_data.items()}
    for key in (
        *RAW_COUNT_KEYS,
        *MOISTURE_KEYS,
        "air_temperature",
        "relative_humidity",
        "illuminance",
    ):
        assert values[key] is None
    assert not any("battery" in key for key in values)


def test_zone_moisture_uses_fixed_100nf_counts_independently() -> None:
    update = parse_frame(FRAME, address=ADDRESS)
    assert update is not None
    data = sensor_update_to_bluetooth_data_update(update, CALIBRATION)
    values = {key.key: value for key, value in data.entity_data.items()}

    assert values["bottom_tsc_count"] == 1000
    assert values["middle_tsc_count"] == 2000
    assert values["top_tsc_count"] == 3000
    assert values["bottom_moisture"] == 100.0
    assert values["middle_moisture"] == pytest.approx(50.0)
    assert values["top_moisture"] == pytest.approx(33.3333333)


def test_missing_calibration_makes_moisture_unavailable() -> None:
    update = parse_frame(FRAME, address=ADDRESS)
    assert update is not None
    data = sensor_update_to_bluetooth_data_update(update)
    values = {key.key: value for key, value in data.entity_data.items()}
    assert all(values[key] is None for key in MOISTURE_KEYS)


async def test_native_units_and_stale_availability(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, service_info_factory
) -> None:
    hass.config_entries.async_update_entry(mock_config_entry, options=CALIBRATION)
    await _setup_with_update(hass, mock_config_entry)
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_config_entry.entry_id)
    by_key = {entry.unique_id.removeprefix(f"{ADDRESS}-"): entry for entry in entries}

    temperature = hass.states.get(by_key["air_temperature"].entity_id)
    assert temperature is not None
    assert temperature.state == "23.45"
    assert temperature.attributes[ATTR_UNIT_OF_MEASUREMENT] == "°C"
    illuminance = hass.states.get(by_key["illuminance"].entity_id)
    assert illuminance is not None
    assert illuminance.state == "123.45"
    assert illuminance.attributes[ATTR_UNIT_OF_MEASUREMENT] == "lx"
    bottom_raw = hass.states.get(by_key["bottom_tsc_count"].entity_id)
    assert bottom_raw is not None
    assert bottom_raw.state == "1000"
    assert ATTR_UNIT_OF_MEASUREMENT not in bottom_raw.attributes
    bottom_moisture = hass.states.get(by_key["bottom_moisture"].entity_id)
    assert bottom_moisture is not None
    assert float(bottom_moisture.state) == 100.0
    assert bottom_moisture.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE

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
    temperature = hass.states.get(by_key["air_temperature"].entity_id)
    assert temperature is not None
    assert temperature.state == "unavailable"
