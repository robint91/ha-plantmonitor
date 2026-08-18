"""Tests for fixed-range TSC soil-moisture conversion."""

import pytest

from custom_components.plant_monitor_ble.calibration import moisture_from_tsc_count


def test_reciprocal_count_interpolation() -> None:
    assert moisture_from_tsc_count(2000, 3000, 1000) == pytest.approx(25.0)
    assert moisture_from_tsc_count(1500, 3000, 1000) == pytest.approx(50.0)


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (4000, 0.0),
        (3000, 0.0),
        (1000, 100.0),
        (500, 100.0),
    ],
)
def test_calibration_boundaries(count: int, expected: float) -> None:
    assert moisture_from_tsc_count(count, 3000, 1000) == expected


@pytest.mark.parametrize(
    ("count", "dry_count", "wet_count"),
    [
        (0, 3000, 1000),
        (-1, 3000, 1000),
        (2000, 0, 1000),
        (2000, 3000, 0),
        (2000, 1000, 1000),
        (2000, 999, 1000),
    ],
)
def test_invalid_calibration_is_unavailable(
    count: int, dry_count: int, wet_count: int
) -> None:
    assert moisture_from_tsc_count(count, dry_count, wet_count) is None
