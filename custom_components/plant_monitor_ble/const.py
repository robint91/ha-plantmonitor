"""Constants for the Plant Monitor BLE integration."""

from datetime import timedelta

DOMAIN = "plant_monitor_ble"
NAME = "Plant Monitor BLE"
INTEGRATION_VERSION = "3.0.0"
CONFIG_ENTRY_VERSION = 4

# Protocol v3 uses one fixed TSC sampling capacitor for every zone.
FIXED_TSC_CAPACITANCE_NF = 100

CONF_BOTTOM_DRY_COUNT = "bottom_dry_count"
CONF_BOTTOM_WET_COUNT = "bottom_wet_count"
CONF_MIDDLE_DRY_COUNT = "middle_dry_count"
CONF_MIDDLE_WET_COUNT = "middle_wet_count"
CONF_TOP_DRY_COUNT = "top_dry_count"
CONF_TOP_WET_COUNT = "top_wet_count"

CALIBRATION_FIELDS = (
    ("bottom", CONF_BOTTOM_DRY_COUNT, CONF_BOTTOM_WET_COUNT),
    ("middle", CONF_MIDDLE_DRY_COUNT, CONF_MIDDLE_WET_COUNT),
    ("top", CONF_TOP_DRY_COUNT, CONF_TOP_WET_COUNT),
)

# Development-only Bluetooth SIG Company Identifier. When a production identifier
# is assigned, update this value, manifest.json's manufacturer_id, and test vectors.
COMPANY_ID = 0xFFFF
PROTOCOL_VERSION = 3
FRAME_LENGTH = 15
DEDUPLICATION_WINDOW = timedelta(seconds=60)

EXPECTED_UPDATE_INTERVAL = timedelta(seconds=30)
# Allow three expected reports to be missed before marking entities unavailable.
STALE_TIMEOUT = timedelta(seconds=90)

# Entity keys removed across earlier protocol migrations. The three moisture
# keys are retained: they represent optional HA-side calibrated moisture rather
# than values carried by the custom packet.
REMOVED_ENTITY_KEYS = frozenset(
    {
        "battery_low",
        "battery_measurement_fault",
        "battery_voltage",
        "ble_fault",
        "bottom_filtered_count",
        "bottom_range",
        "bottom_saturation",
        "bottom_tsc_1nf",
        "bottom_tsc_11nf",
        "bottom_tsc_48nf",
        "calibration_invalid",
        "calibration_revision",
        "environmental_sensor_fault",
        "i2c_fault",
        "middle_filtered_count",
        "middle_range",
        "middle_saturation",
        "middle_tsc_1nf",
        "middle_tsc_11nf",
        "middle_tsc_48nf",
        "oscillator_configuration_fault",
        "status_word",
        "top_filtered_count",
        "top_range",
        "top_saturation",
        "top_tsc_1nf",
        "top_tsc_11nf",
        "top_tsc_48nf",
        "tsc_acquisition_fault",
    }
)
