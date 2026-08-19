"""Fixtures for Plant Monitor BLE tests."""

from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING

import pytest

from custom_components.plant_monitor_ble.const import COMPANY_ID, DOMAIN

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry

ADDRESS = "AA:BB:CC:DD:EE:FF"
CALIBRATION = {
    "bottom_dry_count": 2000,
    "bottom_wet_count": 1000,
    "middle_dry_count": 3000,
    "middle_wet_count": 1500,
    "top_dry_count": 4000,
    "top_wet_count": 2000,
}
FRAME = bytes.fromhex("03 2A E8 03 D0 07 B8 0B 29 09 2E 16 39 30 00")
MANUFACTURER_AD = bytes.fromhex(
    "12 FF FF FF 03 2A E8 03 D0 07 B8 0B 29 09 2E 16 39 30 00"
)


if importlib.util.find_spec("homeassistant") is not None:
    from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
    from homeassistant.const import CONF_ADDRESS
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    @pytest.fixture(autouse=True)
    def auto_enable_custom_integrations(
        enable_custom_integrations: None, mock_bluetooth: None
    ) -> None:
        """Enable custom integrations and mock Bluetooth hardware."""

    @pytest.fixture
    def service_info_factory() -> Callable[..., BluetoothServiceInfoBleak]:
        """Build Bluetooth advertisements accepted by Home Assistant tests."""

        def _make(
            *,
            address: str = ADDRESS,
            frame: bytes = FRAME,
            connectable: bool = False,
            rssi: int = -67,
        ) -> BluetoothServiceInfoBleak:
            manufacturer_data = {COMPANY_ID: frame}
            return BluetoothServiceInfoBleak(
                name="Plant Monitor",
                address=address,
                rssi=rssi,
                manufacturer_data=manufacturer_data,
                service_data={},
                service_uuids=[],
                source="local",
                device=None,  # type: ignore[arg-type]
                advertisement=None,  # type: ignore[arg-type]
                connectable=connectable,
                time=0,
                tx_power=None,
            )

        return _make

    @pytest.fixture
    def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
        """Create a configured integration entry."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Plant Monitor",
            unique_id=ADDRESS,
            data={CONF_ADDRESS: ADDRESS},
        )
        entry.add_to_hass(hass)
        return entry
