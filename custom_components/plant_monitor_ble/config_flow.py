"""Config flow for Plant Monitor BLE."""

from dataclasses import dataclass
from typing import Any, override

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import CONFIG_ENTRY_VERSION, DOMAIN, NAME
from .parser import parse_manufacturer_data


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
