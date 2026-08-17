"""Tests for the pure Plant Monitor protocol parser."""

import struct
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from custom_components.plant_monitor_ble.parser import PacketDeduplicator, parse_frame

from .conftest import ADDRESS, FRAME, LEGACY_FRAME


def _replace_u16(frame: bytes, offset: int, value: int) -> bytes:
    changed = bytearray(frame)
    struct.pack_into("<H", changed, offset, value)
    return bytes(changed)


def test_known_good_vector() -> None:
    received_at = datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc)
    result = parse_frame(
        LEGACY_FRAME, address=ADDRESS, rssi=-67, received_at=received_at
    )
    assert result is not None
    assert result.version == 1
    assert result.packet_id == 42
    assert result.status == 0x0001
    assert result.calibration_revision == 7
    assert (
        result.bottom_range_code,
        result.middle_range_code,
        result.top_range_code,
    ) == (
        0,
        2,
        3,
    )
    assert (
        result.bottom_filtered_count,
        result.middle_filtered_count,
        result.top_filtered_count,
    ) == (1000, 2000, 3000)
    assert result.bottom_moisture == 12.34
    assert result.middle_moisture == 45.67
    assert result.top_moisture == 89.01
    assert result.battery_mv == 2987
    assert result.temperature_c == 23.45
    assert result.humidity == 56.78
    assert result.address == ADDRESS
    assert result.rssi == -67
    assert result.received_at == received_at
    with pytest.raises(FrozenInstanceError):
        result.packet_id = 1  # type: ignore[misc]


def test_signed_negative_temperature() -> None:
    changed = bytearray(FRAME)
    struct.pack_into("<h", changed, 20, -1234)
    result = parse_frame(bytes(changed), address=ADDRESS)
    assert result is not None
    assert result.temperature_raw == -1234
    assert result.temperature_c == -12.34


@pytest.mark.parametrize("offset", [6, 8, 10, 12, 14, 16, 18, 22])
def test_unsigned_invalid_sentinels(offset: int) -> None:
    result = parse_frame(_replace_u16(FRAME, offset, 0xFFFF), address=ADDRESS)
    assert result is not None
    converted = {
        6: result.bottom_filtered_count,
        8: result.middle_filtered_count,
        10: result.top_filtered_count,
        12: result.bottom_moisture,
        14: result.middle_moisture,
        16: result.top_moisture,
        18: result.battery_mv,
        22: result.humidity,
    }
    assert converted[offset] is None
    if offset == 12:
        assert result.bottom_moisture_raw == 0xFFFF


def test_temperature_invalid_sentinel() -> None:
    changed = bytearray(FRAME)
    struct.pack_into("<h", changed, 20, -32768)
    result = parse_frame(bytes(changed), address=ADDRESS)
    assert result is not None
    assert result.temperature_c is None


@pytest.mark.parametrize("frame", [FRAME[:-1], FRAME + b"\x00"])
def test_wrong_frame_length(frame: bytes) -> None:
    assert parse_frame(frame, address=ADDRESS) is None


def test_unsupported_version() -> None:
    assert parse_frame(bytes([2]) + FRAME[1:], address=ADDRESS) is None


def test_reserved_range_bits() -> None:
    changed = bytearray(FRAME)
    changed[5] |= 0x40
    assert parse_frame(bytes(changed), address=ADDRESS) is None


def test_current_firmware_fixed_11_nf_range() -> None:
    changed = bytearray(FRAME)
    changed[5] = 0x15  # range code 1 in all three two-bit fields
    result = parse_frame(bytes(changed), address=ADDRESS)
    assert result is not None
    assert (
        result.bottom_range_code,
        result.middle_range_code,
        result.top_range_code,
    ) == (1, 1, 1)


@pytest.mark.parametrize("offset", [12, 14, 16, 22])
def test_out_of_range_percentages(offset: int) -> None:
    assert parse_frame(_replace_u16(FRAME, offset, 10001), address=ADDRESS) is None


@pytest.mark.parametrize("bit", range(16))
def test_every_status_flag(bit: int) -> None:
    result = parse_frame(_replace_u16(FRAME, 2, 1 << bit), address=ADDRESS)
    assert result is not None
    flags = list(result.flags.as_dict().values())
    assert flags == [index == bit for index in range(16)]


def test_packet_id_duplicate_suppression_and_timeout() -> None:
    deduplicator = PacketDeduplicator()
    assert not deduplicator.is_duplicate(ADDRESS, 42, now=100)
    assert deduplicator.is_duplicate(ADDRESS, 42, now=159.999)
    assert not deduplicator.is_duplicate(ADDRESS, 42, now=160)


def test_packet_id_wraparound() -> None:
    deduplicator = PacketDeduplicator()
    assert not deduplicator.is_duplicate(ADDRESS, 255, now=1)
    assert not deduplicator.is_duplicate(ADDRESS, 0, now=2)


def test_same_packet_id_different_addresses() -> None:
    deduplicator = PacketDeduplicator()
    assert not deduplicator.is_duplicate(ADDRESS, 7, now=1)
    assert not deduplicator.is_duplicate("11:22:33:44:55:66", 7, now=2)
