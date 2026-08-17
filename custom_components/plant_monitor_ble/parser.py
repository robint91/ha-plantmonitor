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
from .types import PlantMonitorAdvertisement

_FRAME: Final = struct.Struct("<BB9HhH")
_INVALID_UNSIGNED: Final = 0xFFFF
_INVALID_ILLUMINANCE: Final = 0xFFFFFF
_INVALID_TEMPERATURE: Final = -32768
_MAX_PERCENTAGE_RAW: Final = 10000


def _optional_unsigned(value: int) -> int | None:
    return None if value == _INVALID_UNSIGNED else value


def _scaled_percentage(value: int) -> float | None:
    return None if value == _INVALID_UNSIGNED else value / 100


def parse_frame(
    frame: bytes,
    *,
    address: str,
    rssi: int | None = None,
    received_at: datetime | None = None,
) -> PlantMonitorAdvertisement | None:
    """Decode a protocol frame, returning None when it is not compatible."""
    if len(frame) < FRAME_LENGTH:
        return None

    (
        version,
        packet_id,
        bottom_tsc_1nf,
        bottom_tsc_11nf,
        bottom_tsc_48nf,
        middle_tsc_1nf,
        middle_tsc_11nf,
        middle_tsc_48nf,
        top_tsc_1nf,
        top_tsc_11nf,
        top_tsc_48nf,
        temperature,
        humidity,
    ) = _FRAME.unpack_from(frame)
    illuminance = int.from_bytes(frame[24:27], "little")

    if version != PROTOCOL_VERSION:
        return None
    if humidity != _INVALID_UNSIGNED and humidity > _MAX_PERCENTAGE_RAW:
        return None

    return PlantMonitorAdvertisement(
        address=address,
        rssi=rssi,
        received_at=received_at or datetime.now(timezone.utc),
        version=version,
        packet_id=packet_id,
        bottom_tsc_1nf_raw=bottom_tsc_1nf,
        bottom_tsc_11nf_raw=bottom_tsc_11nf,
        bottom_tsc_48nf_raw=bottom_tsc_48nf,
        middle_tsc_1nf_raw=middle_tsc_1nf,
        middle_tsc_11nf_raw=middle_tsc_11nf,
        middle_tsc_48nf_raw=middle_tsc_48nf,
        top_tsc_1nf_raw=top_tsc_1nf,
        top_tsc_11nf_raw=top_tsc_11nf,
        top_tsc_48nf_raw=top_tsc_48nf,
        bottom_tsc_1nf=_optional_unsigned(bottom_tsc_1nf),
        bottom_tsc_11nf=_optional_unsigned(bottom_tsc_11nf),
        bottom_tsc_48nf=_optional_unsigned(bottom_tsc_48nf),
        middle_tsc_1nf=_optional_unsigned(middle_tsc_1nf),
        middle_tsc_11nf=_optional_unsigned(middle_tsc_11nf),
        middle_tsc_48nf=_optional_unsigned(middle_tsc_48nf),
        top_tsc_1nf=_optional_unsigned(top_tsc_1nf),
        top_tsc_11nf=_optional_unsigned(top_tsc_11nf),
        top_tsc_48nf=_optional_unsigned(top_tsc_48nf),
        temperature_raw=temperature,
        temperature_c=(
            None if temperature == _INVALID_TEMPERATURE else temperature / 100
        ),
        humidity_raw=humidity,
        humidity=_scaled_percentage(humidity),
        illuminance_raw=illuminance,
        illuminance_lux=(
            None if illuminance == _INVALID_ILLUMINANCE else illuminance / 100
        ),
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
