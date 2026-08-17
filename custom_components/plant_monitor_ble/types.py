"""Data types for the Plant Monitor BLE integration."""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import PlantMonitorBluetoothCoordinator


@dataclass(frozen=True, slots=True)
class StatusFlags:
    """Decoded protocol status flags."""

    calibration_valid: bool
    calibration_invalid: bool
    bottom_saturation: bool
    middle_saturation: bool
    top_saturation: bool
    tsc_acquisition_error: bool
    hdc3022_error: bool
    opt3001_error: bool
    battery_low: bool
    fallback_calibration: bool
    battery_measurement_error: bool
    i2c_error: bool
    ble_fault: bool
    oscillator_fault: bool
    build_configuration_invalid: bool
    reserved: bool

    def as_dict(self) -> dict[str, bool]:
        """Return a serializable representation."""
        return {
            "calibration_valid": self.calibration_valid,
            "calibration_invalid": self.calibration_invalid,
            "bottom_saturation": self.bottom_saturation,
            "middle_saturation": self.middle_saturation,
            "top_saturation": self.top_saturation,
            "tsc_acquisition_error": self.tsc_acquisition_error,
            "hdc3022_error": self.hdc3022_error,
            "opt3001_error": self.opt3001_error,
            "battery_low": self.battery_low,
            "fallback_calibration": self.fallback_calibration,
            "battery_measurement_error": self.battery_measurement_error,
            "i2c_error": self.i2c_error,
            "ble_fault": self.ble_fault,
            "oscillator_fault": self.oscillator_fault,
            "build_configuration_invalid": self.build_configuration_invalid,
            "reserved": self.reserved,
        }


@dataclass(frozen=True, slots=True)
class PlantMonitorAdvertisement:
    """Decoded immutable Plant Monitor advertisement."""

    address: str
    rssi: int | None
    received_at: datetime
    version: int
    packet_id: int
    status: int
    flags: StatusFlags
    calibration_revision: int
    bottom_range_code: int
    middle_range_code: int
    top_range_code: int
    bottom_filtered_raw: int
    middle_filtered_raw: int
    top_filtered_raw: int
    bottom_filtered_count: int | None
    middle_filtered_count: int | None
    top_filtered_count: int | None
    bottom_moisture_raw: int
    middle_moisture_raw: int
    top_moisture_raw: int
    bottom_moisture: float | None
    middle_moisture: float | None
    top_moisture: float | None
    battery_mv_raw: int
    battery_mv: int | None
    temperature_raw: int
    temperature_c: float | None
    humidity_raw: int
    humidity: float | None

    @property
    def validity(self) -> dict[str, bool]:
        """Return validity for fields that support an invalid sentinel."""
        return {
            "bottom_filtered_count": self.bottom_filtered_count is not None,
            "middle_filtered_count": self.middle_filtered_count is not None,
            "top_filtered_count": self.top_filtered_count is not None,
            "bottom_moisture": self.bottom_moisture is not None,
            "middle_moisture": self.middle_moisture is not None,
            "top_moisture": self.top_moisture is not None,
            "battery_voltage": self.battery_mv is not None,
            "air_temperature": self.temperature_c is not None,
            "relative_humidity": self.humidity is not None,
            "rssi": self.rssi is not None,
        }


if TYPE_CHECKING:
    PlantMonitorConfigEntry: TypeAlias = ConfigEntry[PlantMonitorBluetoothCoordinator]
else:
    PlantMonitorConfigEntry: TypeAlias = Any
