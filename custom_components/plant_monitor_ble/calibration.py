"""Soil-moisture calibration for fixed-range STM32 TSC measurements."""


def moisture_from_tsc_count(
    count: int,
    dry_count: int,
    wet_count: int,
) -> float | None:
    """Convert a fixed-range STM32 TSC count to moisture percentage."""
    if count <= 0 or wet_count <= 0 or dry_count <= 0:
        return None

    if dry_count <= wet_count:
        return None

    if count >= dry_count:
        return 0.0

    if count <= wet_count:
        return 100.0

    moisture = (
        100.0 * wet_count * (dry_count - count) / (count * (dry_count - wet_count))
    )

    return max(0.0, min(100.0, moisture))
