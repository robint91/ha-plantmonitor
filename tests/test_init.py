"""Tests for Plant Monitor BLE setup and unload."""

from unittest.mock import patch

import pytest

pytest.importorskip("homeassistant")

from homeassistant import loader
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.plant_monitor_ble import async_migrate_entry
from custom_components.plant_monitor_ble.const import DOMAIN

from .conftest import ADDRESS


async def test_setup_and_unload(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    with patch(
        "custom_components.plant_monitor_ble.coordinator."
        "PlantMonitorBluetoothCoordinator.async_start",
        return_value=lambda: None,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.runtime_data.expected_update_interval_seconds == 30
    assert mock_config_entry.runtime_data.stale_timeout_seconds == 90

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_manifest_loads(hass: HomeAssistant) -> None:
    integration = await loader.async_get_integration(hass, DOMAIN)
    assert integration.manifest["version"] == "1.1.0"
    assert integration.manifest["iot_class"] == "local_push"
    assert integration.manifest["bluetooth"] == [
        {
            "connectable": False,
            "manufacturer_id": 65535,
            "manufacturer_data_start": [1],
        }
    ]


async def test_migrate_removes_obsolete_range_entities(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    registry = er.async_get(hass)
    old_entity = registry.async_get_or_create(
        domain=Platform.SENSOR,
        platform=DOMAIN,
        unique_id=f"{ADDRESS}-bottom_range",
        config_entry=mock_config_entry,
    )

    assert await async_migrate_entry(hass, mock_config_entry)
    assert mock_config_entry.version == 2
    assert dict(mock_config_entry.data) == {CONF_ADDRESS: ADDRESS}
    assert registry.async_get(old_entity.entity_id) is None
