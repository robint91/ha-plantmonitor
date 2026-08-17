"""Data types for the Plant Monitor BLE integration."""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import PlantMonitorBluetoothCoordinator


@dataclass(frozen=True, slots=True)
class PlantMonitorAdvertisement:
    """Decoded immutable protocol-v2 Plant Monitor advertisement."""

    address: str
    rssi: int | None
    received_at: datetime
    version: int
    packet_id: int
    bottom_tsc_1nf_raw: int
    bottom_tsc_11nf_raw: int
    bottom_tsc_48nf_raw: int
    middle_tsc_1nf_raw: int
    middle_tsc_11nf_raw: int
    middle_tsc_48nf_raw: int
    top_tsc_1nf_raw: int
    top_tsc_11nf_raw: int
    top_tsc_48nf_raw: int
    bottom_tsc_1nf: int | None
    bottom_tsc_11nf: int | None
    bottom_tsc_48nf: int | None
    middle_tsc_1nf: int | None
    middle_tsc_11nf: int | None
    middle_tsc_48nf: int | None
    top_tsc_1nf: int | None
    top_tsc_11nf: int | None
    top_tsc_48nf: int | None
    temperature_raw: int
    temperature_c: float | None
    humidity_raw: int
    humidity: float | None
    illuminance_raw: int
    illuminance_lux: float | None

    @property
    def validity(self) -> dict[str, bool]:
        """Return validity for fields that support an invalid sentinel."""
        return {
            "bottom_tsc_1nf": self.bottom_tsc_1nf is not None,
            "bottom_tsc_11nf": self.bottom_tsc_11nf is not None,
            "bottom_tsc_48nf": self.bottom_tsc_48nf is not None,
            "middle_tsc_1nf": self.middle_tsc_1nf is not None,
            "middle_tsc_11nf": self.middle_tsc_11nf is not None,
            "middle_tsc_48nf": self.middle_tsc_48nf is not None,
            "top_tsc_1nf": self.top_tsc_1nf is not None,
            "top_tsc_11nf": self.top_tsc_11nf is not None,
            "top_tsc_48nf": self.top_tsc_48nf is not None,
            "air_temperature": self.temperature_c is not None,
            "relative_humidity": self.humidity is not None,
            "illuminance": self.illuminance_lux is not None,
            "rssi": self.rssi is not None,
        }


if TYPE_CHECKING:
    PlantMonitorConfigEntry: TypeAlias = ConfigEntry[PlantMonitorBluetoothCoordinator]
else:
    PlantMonitorConfigEntry: TypeAlias = Any
