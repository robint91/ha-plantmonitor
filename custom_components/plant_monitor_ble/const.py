"""Constants for the Plant Monitor BLE integration."""

from datetime import timedelta

DOMAIN = "plant_monitor_ble"
NAME = "Plant Monitor BLE"
INTEGRATION_VERSION = "2.0.0"
CONFIG_ENTRY_VERSION = 3

# Development-only Bluetooth SIG Company Identifier. When a production identifier
# is assigned, update this value, manifest.json's manufacturer_id, and test vectors.
COMPANY_ID = 0xFFFF
PROTOCOL_VERSION = 2
FRAME_LENGTH = 27
DEDUPLICATION_WINDOW = timedelta(seconds=60)

EXPECTED_UPDATE_INTERVAL = timedelta(seconds=30)
# Allow three expected reports to be missed before marking entities unavailable.
STALE_TIMEOUT = timedelta(seconds=90)

# Entity keys removed across the v1.1 and protocol-v2 migrations. Protocol v2
# contains neither firmware-calibrated moisture nor status and battery fields.
REMOVED_ENTITY_KEYS = frozenset(
    {
        "battery_low",
        "battery_measurement_fault",
        "battery_voltage",
        "ble_fault",
        "bottom_filtered_count",
        "bottom_moisture",
        "bottom_range",
        "bottom_saturation",
        "calibration_invalid",
        "calibration_revision",
        "environmental_sensor_fault",
        "i2c_fault",
        "middle_filtered_count",
        "middle_moisture",
        "middle_range",
        "middle_saturation",
        "oscillator_configuration_fault",
        "status_word",
        "top_filtered_count",
        "top_moisture",
        "top_range",
        "top_saturation",
        "tsc_acquisition_fault",
    }
)
