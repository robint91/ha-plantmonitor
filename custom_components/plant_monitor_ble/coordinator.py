"""Bluetooth coordinator for Plant Monitor BLE."""

from datetime import datetime
from logging import Logger
from typing import override

from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later

from .const import EXPECTED_UPDATE_INTERVAL, STALE_TIMEOUT
from .parser import PacketDeduplicator, parse_manufacturer_data
from .types import PlantMonitorAdvertisement


class PlantMonitorBluetoothCoordinator(
    PassiveBluetoothProcessorCoordinator[PlantMonitorAdvertisement | None]
):
    """Coordinate passive advertisements from one plant monitor."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: Logger,
        address: str,
        mode: BluetoothScanningMode,
        *,
        connectable: bool = False,
    ) -> None:
        """Initialize the passive coordinator."""
        self.latest_update: PlantMonitorAdvertisement | None = None
        self._deduplicator = PacketDeduplicator()
        self._cancel_stale: CALLBACK_TYPE | None = None
        self._last_service_info: BluetoothServiceInfoBleak | None = None
        super().__init__(
            hass, logger, address, mode, self.process_advertisement, connectable
        )

    @property
    def expected_update_interval_seconds(self) -> float:
        """Return the firmware's expected measurement interval."""
        return EXPECTED_UPDATE_INTERVAL.total_seconds()

    @property
    def stale_timeout_seconds(self) -> float:
        """Return the deadline after which the last report is stale."""
        return STALE_TIMEOUT.total_seconds()

    @callback
    def _schedule_stale_timeout(self, service_info: BluetoothServiceInfoBleak) -> None:
        """Schedule unavailability after three missed firmware reports."""
        if self._cancel_stale is not None:
            self._cancel_stale()
        self._last_service_info = service_info
        self._cancel_stale = async_call_later(
            self.hass, self.stale_timeout_seconds, self._async_mark_stale
        )

    @callback
    def _async_mark_stale(self, _now: datetime) -> None:
        """Mark the device unavailable when no fresh report arrived."""
        self._cancel_stale = None
        if self._last_service_info is not None:
            self._async_handle_unavailable(self._last_service_info)

    @callback
    @override
    def _async_handle_unavailable(
        self, service_info: BluetoothServiceInfoBleak
    ) -> None:
        """Cancel the local deadline and dispatch unavailability."""
        if self._cancel_stale is not None:
            self._cancel_stale()
            self._cancel_stale = None
        super()._async_handle_unavailable(service_info)

    @callback
    @override
    def _async_stop(self) -> None:
        """Stop Bluetooth callbacks and the local stale deadline."""
        if self._cancel_stale is not None:
            self._cancel_stale()
            self._cancel_stale = None
        super()._async_stop()

    def process_advertisement(
        self, service_info: BluetoothServiceInfoBleak
    ) -> PlantMonitorAdvertisement | None:
        """Validate, deduplicate, and store an advertisement."""
        update = parse_manufacturer_data(
            service_info.manufacturer_data,
            address=service_info.address,
            rssi=service_info.rssi,
        )
        if update is None:
            return None
        self._schedule_stale_timeout(service_info)
        if self._deduplicator.is_duplicate(update.address, update.packet_id):
            return None
        self.latest_update = update
        return update


class PlantMonitorBluetoothDataProcessor[T](
    PassiveBluetoothDataProcessor[T, PlantMonitorAdvertisement | None]
):
    """Typed passive data processor for Plant Monitor updates."""

    coordinator: PlantMonitorBluetoothCoordinator
