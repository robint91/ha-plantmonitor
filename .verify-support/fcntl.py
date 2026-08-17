"""Minimal Windows test-environment stub for Home Assistant's runner import."""

LOCK_EX = 2
LOCK_NB = 4


def flock(_file_descriptor: int, _operation: int) -> None:
    """No-op because tests do not start a second Home Assistant process."""
