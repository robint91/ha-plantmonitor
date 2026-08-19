"""Tests for the pure Plant Monitor protocol-v3 parser."""

import struct
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from custom_components.plant_monitor_ble.const import COMPANY_ID
from custom_components.plant_monitor_ble.parser import (
    PacketDeduplicator,
    parse_frame,
    parse_manufacturer_data,
)

from .conftest import ADDRESS, FRAME, MANUFACTURER_AD


def _replace_u16(frame: bytes, offset: int, value: int) -> bytes:
    changed = bytearray(frame)
    struct.pack_into("<H", changed, offset, value)
    return bytes(changed)


def test_exact_firmware_vector() -> None:
    assert len(FRAME) == 15
    assert len(MANUFACTURER_AD) == 19
    assert MANUFACTURER_AD == b"\x12\xff\xff\xff" + FRAME
    received_at = datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc)
    result = parse_frame(FRAME, address=ADDRESS, rssi=-67, received_at=received_at)
    assert result is not None
    assert result.version == 3
    assert result.packet_id == 42
    assert result.bottom_tsc == 1000
    assert result.middle_tsc == 2000
    assert result.top_tsc == 3000
    assert result.temperature_c == 23.45
    assert result.humidity == 56.78
    assert result.illuminance_lux == 123.45
    assert result.address == ADDRESS
    assert result.rssi == -67
    assert result.received_at == received_at
    with pytest.raises(FrozenInstanceError):
        result.packet_id = 1  # type: ignore[misc]


def test_signed_negative_temperature() -> None:
    changed = bytearray(FRAME)
    struct.pack_into("<h", changed, 8, -1234)
    result = parse_frame(bytes(changed), address=ADDRESS)
    assert result is not None
    assert result.temperature_raw == -1234
    assert result.temperature_c == -12.34


@pytest.mark.parametrize(
    ("offset", "field"),
    [(2, "bottom_tsc"), (4, "middle_tsc"), (6, "top_tsc")],
)
def test_tsc_invalid_sentinels_preserve_raw_value(offset: int, field: str) -> None:
    result = parse_frame(_replace_u16(FRAME, offset, 0xFFFF), address=ADDRESS)
    assert result is not None
    assert getattr(result, field) is None
    assert getattr(result, f"{field}_raw") == 0xFFFF


def test_environmental_invalid_sentinels() -> None:
    changed = bytearray(FRAME)
    changed[8:10] = b"\x00\x80"
    changed[10:12] = b"\xff\xff"
    changed[12:15] = b"\xff\xff\xff"
    result = parse_frame(bytes(changed), address=ADDRESS)
    assert result is not None
    assert result.temperature_c is None
    assert result.humidity is None
    assert result.illuminance_lux is None
    assert result.temperature_raw == -32768
    assert result.humidity_raw == 0xFFFF
    assert result.illuminance_raw == 0xFFFFFF


@pytest.mark.parametrize("length", [0, 1, 14])
def test_incorrect_frame_length(length: int) -> None:
    assert parse_frame(FRAME[:length], address=ADDRESS) is None


def test_trailing_byte_is_rejected() -> None:
    assert parse_frame(FRAME + b"\xaa", address=ADDRESS) is None


@pytest.mark.parametrize("version", [0, 1, 2, 255])
def test_unsupported_version(version: int) -> None:
    assert parse_frame(bytes([version]) + FRAME[1:], address=ADDRESS) is None


def test_out_of_range_humidity() -> None:
    assert parse_frame(_replace_u16(FRAME, 10, 10001), address=ADDRESS) is None


def test_manufacturer_data_company_id() -> None:
    assert parse_manufacturer_data({COMPANY_ID: FRAME}, address=ADDRESS) is not None
    assert parse_manufacturer_data({0x1234: FRAME}, address=ADDRESS) is None


def test_custom_payload_has_no_battery_or_firmware_moisture() -> None:
    result = parse_frame(FRAME, address=ADDRESS)
    assert result is not None
    for field in (
        "battery_mv",
        "battery_percentage",
        "bottom_moisture",
        "middle_moisture",
        "top_moisture",
        "calibration_revision",
        "status",
    ):
        assert not hasattr(result, field)


def test_packet_id_duplicate_suppression_and_timeout() -> None:
    deduplicator = PacketDeduplicator()
    assert not deduplicator.is_duplicate(ADDRESS, 42, now=100)
    assert deduplicator.is_duplicate(ADDRESS, 42, now=159.999)
    assert not deduplicator.is_duplicate(ADDRESS, 42, now=160)


def test_packet_id_rollover() -> None:
    deduplicator = PacketDeduplicator()
    assert not deduplicator.is_duplicate(ADDRESS, 255, now=1)
    assert not deduplicator.is_duplicate(ADDRESS, 0, now=2)
    assert not deduplicator.is_duplicate(ADDRESS, 255, now=3)


def test_same_packet_id_different_addresses() -> None:
    deduplicator = PacketDeduplicator()
    assert not deduplicator.is_duplicate(ADDRESS, 7, now=1)
    assert not deduplicator.is_duplicate("11:22:33:44:55:66", 7, now=2)
