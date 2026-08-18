"""Tests for the Plant Monitor BLE config flow."""

from unittest.mock import patch

import pytest

pytest.importorskip("homeassistant")

from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.plant_monitor_ble.const import DOMAIN

from .conftest import ADDRESS, CALIBRATION, FRAME


async def test_valid_bluetooth_discovery_and_confirmation(
    hass: HomeAssistant, service_info_factory
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=service_info_factory(),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_ADDRESS: ADDRESS}
    assert result["result"].unique_id == ADDRESS
    assert result["result"].version == 3


async def test_user_discovery_selection(
    hass: HomeAssistant, service_info_factory
) -> None:
    with patch(
        "custom_components.plant_monitor_ble.config_flow.async_discovered_service_info",
        return_value=[service_info_factory()],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"


async def test_duplicate_device(hass: HomeAssistant, service_info_factory) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=service_info_factory(),
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_duplicate_discovery_flow(
    hass: HomeAssistant, service_info_factory
) -> None:
    first = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=service_info_factory(),
    )
    assert first["type"] is FlowResultType.FORM

    second = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=service_info_factory(),
    )
    assert second["type"] is FlowResultType.ABORT
    assert second["reason"] == "already_in_progress"


async def test_malformed_payload(hass: HomeAssistant, service_info_factory) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=service_info_factory(frame=FRAME[:-1]),
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_supported"


async def test_connectable_scanner_report_is_supported(
    hass: HomeAssistant, service_info_factory
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=service_info_factory(connectable=True),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"


async def test_no_compatible_devices_found(hass: HomeAssistant) -> None:
    with patch(
        "custom_components.plant_monitor_ble.config_flow.async_discovered_service_info",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_calibration_options_flow(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], CALIBRATION
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == CALIBRATION


async def test_calibration_options_reject_reversed_points(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    invalid = {**CALIBRATION, "bottom_dry_count": 1000}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], invalid
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_calibration"}
