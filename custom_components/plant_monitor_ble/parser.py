"""Pure parser for Plant Monitor BLE manufacturer data."""

import struct
import time
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Final

from .const import (
    COMPANY_ID,
    DEDUPLICATION_WINDOW,
    FRAME_LENGTH,
    PROTOCOL_VERSION,
)
from .types import PlantMonitorAdvertisement, StatusFlags

_FRAME: Final = struct.Struct("<BBHBBHHHHHHHhH")
_INVALID_UNSIGNED: Final = 0xFFFF
_INVALID_TEMPERATURE: Final = -32768
_MAX_PERCENTAGE_RAW: Final = 10000


def _optional_unsigned(value: int) -> int | None:
    return None if value == _INVALID_UNSIGNED else value


def _scaled_percentage(value: int) -> float | None:
    return None if value == _INVALID_UNSIGNED else value / 100


def _decode_flags(status: int) -> StatusFlags:
    bits = tuple(bool(status & (1 << bit)) for bit in range(16))
    return StatusFlags(*bits)


def parse_frame(
    frame: bytes,
    *,
    address: str,
    rssi: int | None = None,
    received_at: datetime | None = None,
) -> PlantMonitorAdvertisement | None:
    """Decode a protocol frame, returning None when it is not compatible."""
    if len(frame) != FRAME_LENGTH:
        return None

    (
        version,
        packet_id,
        status,
        revision,
        range_byte,
        bottom_filtered,
        middle_filtered,
        top_filtered,
        bottom_moisture,
        middle_moisture,
        top_moisture,
        battery_mv,
        temperature,
        humidity,
    ) = _FRAME.unpack(frame)

    if version != PROTOCOL_VERSION or range_byte & 0xC0:
        return None
    moisture_values = (bottom_moisture, middle_moisture, top_moisture)
    if any(
        value != _INVALID_UNSIGNED and value > _MAX_PERCENTAGE_RAW
        for value in moisture_values
    ):
        return None
    if humidity != _INVALID_UNSIGNED and humidity > _MAX_PERCENTAGE_RAW:
        return None

    bottom_range = range_byte & 0x03
    middle_range = (range_byte >> 2) & 0x03
    top_range = (range_byte >> 4) & 0x03
    if any(code not in range(4) for code in (bottom_range, middle_range, top_range)):
        return None

    return PlantMonitorAdvertisement(
        address=address,
        rssi=rssi,
        received_at=received_at or datetime.now(timezone.utc),
        version=version,
        packet_id=packet_id,
        status=status,
        flags=_decode_flags(status),
        calibration_revision=revision,
        bottom_range_code=bottom_range,
        middle_range_code=middle_range,
        top_range_code=top_range,
        bottom_filtered_raw=bottom_filtered,
        middle_filtered_raw=middle_filtered,
        top_filtered_raw=top_filtered,
        bottom_filtered_count=_optional_unsigned(bottom_filtered),
        middle_filtered_count=_optional_unsigned(middle_filtered),
        top_filtered_count=_optional_unsigned(top_filtered),
        bottom_moisture_raw=bottom_moisture,
        middle_moisture_raw=middle_moisture,
        top_moisture_raw=top_moisture,
        bottom_moisture=_scaled_percentage(bottom_moisture),
        middle_moisture=_scaled_percentage(middle_moisture),
        top_moisture=_scaled_percentage(top_moisture),
        battery_mv_raw=battery_mv,
        battery_mv=_optional_unsigned(battery_mv),
        temperature_raw=temperature,
        temperature_c=(
            None if temperature == _INVALID_TEMPERATURE else temperature / 100
        ),
        humidity_raw=humidity,
        humidity=_scaled_percentage(humidity),
    )


def parse_manufacturer_data(
    manufacturer_data: Mapping[int, bytes],
    *,
    address: str,
    rssi: int | None = None,
    received_at: datetime | None = None,
) -> PlantMonitorAdvertisement | None:
    """Parse Home Assistant manufacturer data for this protocol."""
    frame = manufacturer_data.get(COMPANY_ID)
    if frame is None:
        return None
    return parse_frame(frame, address=address, rssi=rssi, received_at=received_at)


class PacketDeduplicator:
    """Suppress burst duplicates per address for a bounded time window."""

    def __init__(self, window: float = DEDUPLICATION_WINDOW.total_seconds()) -> None:
        """Initialize a deduplicator with a bounded window in seconds."""
        self._window = window
        self._last: dict[str, tuple[int, float]] = {}

    def is_duplicate(
        self, address: str, packet_id: int, *, now: float | None = None
    ) -> bool:
        """Return whether this address/packet pair is a recent duplicate."""
        timestamp = time.monotonic() if now is None else now
        previous = self._last.get(address)
        if previous is not None and previous[0] == packet_id:
            elapsed = timestamp - previous[1]
            if 0 <= elapsed < self._window:
                return True
        self._last[address] = (packet_id, timestamp)
        return False
