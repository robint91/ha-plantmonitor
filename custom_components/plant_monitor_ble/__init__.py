"""Plant Monitor BLE integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from .types import PlantMonitorConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate entries from the autoscaling-era entity model."""
    from homeassistant.helpers import entity_registry as er

    from .const import CONFIG_ENTRY_VERSION, REMOVED_RANGE_ENTITY_KEYS

    if entry.version > CONFIG_ENTRY_VERSION:
        return False
    if entry.version == CONFIG_ENTRY_VERSION:
        return True

    registry = er.async_get(hass)
    address = entry.unique_id
    if address is not None:
        removed_unique_ids = {f"{address}-{key}" for key in REMOVED_RANGE_ENTITY_KEYS}
        for registry_entry in er.async_entries_for_config_entry(
            registry, entry.entry_id
        ):
            if registry_entry.unique_id in removed_unique_ids:
                registry.async_remove(registry_entry.entity_id)

    # Released v1 entries contain only the Bluetooth address. No HA-side
    # calibration values existed to transform; firmware remains authoritative.
    hass.config_entries.async_update_entry(entry, version=CONFIG_ENTRY_VERSION)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: PlantMonitorConfigEntry
) -> bool:
    """Set up Plant Monitor BLE from a config entry."""
    from homeassistant.components.bluetooth import BluetoothScanningMode
    from homeassistant.const import Platform

    from .coordinator import PlantMonitorBluetoothCoordinator

    address = entry.unique_id
    if address is None:
        msg = "Plant Monitor BLE config entry has no Bluetooth address"
        raise ValueError(msg)

    coordinator = PlantMonitorBluetoothCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.PASSIVE,
        connectable=False,
    )
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(
        entry, (Platform.SENSOR, Platform.BINARY_SENSOR)
    )
    entry.async_on_unload(coordinator.async_start())
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: PlantMonitorConfigEntry
) -> bool:
    """Unload a Plant Monitor BLE config entry."""
    from homeassistant.const import Platform

    return await hass.config_entries.async_unload_platforms(
        entry, (Platform.SENSOR, Platform.BINARY_SENSOR)
    )
