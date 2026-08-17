"""Diagnostics for Plant Monitor BLE."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant

from .const import INTEGRATION_VERSION
from .types import PlantMonitorConfigEntry

_TO_REDACT = {CONF_ADDRESS, "address", "unique_id"}


async def async_get_config_entry_diagnostics(
    _hass: HomeAssistant, entry: PlantMonitorConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostics for a config entry."""
    update = entry.runtime_data.latest_update
    latest: dict[str, Any] | None = None
    if update is not None:
        latest = {
            "address": update.address,
            "protocol_version": update.version,
            "packet_id": update.packet_id,
            "field_validity": update.validity,
            "raw_values": {
                "bottom_tsc_1nf": update.bottom_tsc_1nf_raw,
                "bottom_tsc_11nf": update.bottom_tsc_11nf_raw,
                "bottom_tsc_48nf": update.bottom_tsc_48nf_raw,
                "middle_tsc_1nf": update.middle_tsc_1nf_raw,
                "middle_tsc_11nf": update.middle_tsc_11nf_raw,
                "middle_tsc_48nf": update.middle_tsc_48nf_raw,
                "top_tsc_1nf": update.top_tsc_1nf_raw,
                "top_tsc_11nf": update.top_tsc_11nf_raw,
                "top_tsc_48nf": update.top_tsc_48nf_raw,
                "temperature": update.temperature_raw,
                "humidity": update.humidity_raw,
                "illuminance": update.illuminance_raw,
            },
            "last_advertisement": update.received_at.isoformat(),
        }
    return {
        "integration_version": INTEGRATION_VERSION,
        "entry_data": async_redact_data(dict(entry.data), _TO_REDACT),
        "expected_update_interval_seconds": (
            entry.runtime_data.expected_update_interval_seconds
        ),
        "stale_timeout_seconds": entry.runtime_data.stale_timeout_seconds,
        "latest_advertisement": async_redact_data(latest, _TO_REDACT)
        if latest is not None
        else None,
    }
