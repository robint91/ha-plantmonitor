"""Diagnostics for Plant Monitor BLE."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant

from .const import (
    FIXED_TSC_CAPACITANCE_NF,
    FIXED_TSC_RANGE_CODE,
    INTEGRATION_VERSION,
)
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
            "status_word": f"0x{update.status:04X}",
            "status_flags": update.flags.as_dict(),
            "calibration_revision": update.calibration_revision,
            "fixed_tsc_configuration": {
                "expected_range_code": FIXED_TSC_RANGE_CODE,
                "nominal_capacitance_nf": FIXED_TSC_CAPACITANCE_NF,
                "transmitted_range_codes": {
                    "bottom": update.bottom_range_code,
                    "middle": update.middle_range_code,
                    "top": update.top_range_code,
                },
                "matches_current_firmware": all(
                    code == FIXED_TSC_RANGE_CODE
                    for code in (
                        update.bottom_range_code,
                        update.middle_range_code,
                        update.top_range_code,
                    )
                ),
            },
            "field_validity": update.validity,
            "raw_values": {
                "bottom_filtered": update.bottom_filtered_raw,
                "middle_filtered": update.middle_filtered_raw,
                "top_filtered": update.top_filtered_raw,
                "bottom_moisture": update.bottom_moisture_raw,
                "middle_moisture": update.middle_moisture_raw,
                "top_moisture": update.top_moisture_raw,
                "battery_mv": update.battery_mv_raw,
                "temperature": update.temperature_raw,
                "humidity": update.humidity_raw,
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
