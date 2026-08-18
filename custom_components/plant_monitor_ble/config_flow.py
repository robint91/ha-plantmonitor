"""Config flow for Plant Monitor BLE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback

from .const import (
    CALIBRATION_FIELDS,
    CONF_BOTTOM_DRY_COUNT,
    CONF_BOTTOM_WET_COUNT,
    CONF_MIDDLE_DRY_COUNT,
    CONF_MIDDLE_WET_COUNT,
    CONF_TOP_DRY_COUNT,
    CONF_TOP_WET_COUNT,
    CONFIG_ENTRY_VERSION,
    DOMAIN,
    NAME,
)
from .parser import parse_manufacturer_data

_CALIBRATION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BOTTOM_DRY_COUNT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=0xFFFE)
        ),
        vol.Required(CONF_BOTTOM_WET_COUNT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=0xFFFE)
        ),
        vol.Required(CONF_MIDDLE_DRY_COUNT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=0xFFFE)
        ),
        vol.Required(CONF_MIDDLE_WET_COUNT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=0xFFFE)
        ),
        vol.Required(CONF_TOP_DRY_COUNT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=0xFFFE)
        ),
        vol.Required(CONF_TOP_WET_COUNT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=0xFFFE)
        ),
    }
)


@dataclass(frozen=True, slots=True)
class Discovery:
    """A compatible discovered plant monitor."""

    title: str
    service_info: BluetoothServiceInfoBleak


def _supported(service_info: BluetoothServiceInfoBleak) -> bool:
    return (
        parse_manufacturer_data(
            service_info.manufacturer_data,
            address=service_info.address,
            rssi=service_info.rssi,
        )
        is not None
    )


def _title(service_info: BluetoothServiceInfoBleak) -> str:
    name = service_info.name.strip() if service_info.name else ""
    return name if name and name != service_info.address else NAME


class PlantMonitorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Plant Monitor BLE config flow."""

    VERSION = CONFIG_ENTRY_VERSION

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, Discovery] = {}

    @staticmethod
    @callback
    @override
    def async_get_options_flow(_config_entry: ConfigEntry) -> PlantMonitorOptionsFlow:
        """Create the soil-calibration options flow."""
        return PlantMonitorOptionsFlow()

    @override
    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle automatic Bluetooth discovery."""
        if not _supported(discovery_info):
            return self.async_abort(reason="not_supported")
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {"name": _title(discovery_info)}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a discovered device before creating its entry."""
        if user_input is not None:
            if self._discovery_info is None:
                return self.async_abort(reason="not_supported")
            return self.async_create_entry(
                title=_title(self._discovery_info),
                data={CONF_ADDRESS: self._discovery_info.address},
            )
        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=self.context.get("title_placeholders"),
        )

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user select a currently discovered compatible device."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            discovery = self._discovered_devices.get(address)
            if discovery is None or not _supported(discovery.service_info):
                return self.async_abort(reason="not_supported")
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            self._discovery_info = discovery.service_info
            self.context["title_placeholders"] = {"name": discovery.title}
            return await self.async_step_bluetooth_confirm()

        current_addresses = self._async_current_ids(include_ignore=False)
        for service_info in async_discovered_service_info(self.hass, False):
            address = service_info.address
            if address in current_addresses or address in self._discovered_devices:
                continue
            if _supported(service_info):
                self._discovered_devices[address] = Discovery(
                    _title(service_info), service_info
                )
        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")
        titles = {
            address: discovery.title
            for address, discovery in self._discovered_devices.items()
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(titles)}),
        )


class PlantMonitorOptionsFlow(OptionsFlowWithReload):
    """Handle per-zone soil-calibration options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure fixed-range dry and wet TSC counts."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if all(
                user_input[dry_key] > user_input[wet_key]
                for _, dry_key, wet_key in CALIBRATION_FIELDS
            ):
                return self.async_create_entry(data=user_input)
            errors["base"] = "invalid_calibration"

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                _CALIBRATION_SCHEMA,
                user_input if user_input is not None else self.config_entry.options,
            ),
            errors=errors,
        )
