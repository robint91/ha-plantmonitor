"""Minimal Windows test-environment stub for POSIX resource limits."""

RLIMIT_NOFILE = 7


def getrlimit(_resource: int) -> tuple[int, int]:
    """Return generous synthetic limits for tests."""
    return (2048, 2048)


def setrlimit(_resource: int, _limits: tuple[int, int]) -> None:
    """No-op because Windows does not expose POSIX resource limits."""
