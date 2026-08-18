"""Constants for the Plant Monitor BLE integration."""

from datetime import timedelta

DOMAIN = "plant_monitor_ble"
NAME = "Plant Monitor BLE"
INTEGRATION_VERSION = "2.1.0"
CONFIG_ENTRY_VERSION = 3

# The firmware uses one fixed TSC sampling-capacitor/gain configuration for
# moisture conversion. Protocol v2 also reports the other diagnostic readings,
# but calibration deliberately consumes only the fixed 11 nF reading.
FIXED_TSC_CAPACITANCE_NF = 11

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
PROTOCOL_VERSION = 2
FRAME_LENGTH = 27
DEDUPLICATION_WINDOW = timedelta(seconds=60)

EXPECTED_UPDATE_INTERVAL = timedelta(seconds=30)
# Allow three expected reports to be missed before marking entities unavailable.
STALE_TIMEOUT = timedelta(seconds=90)

# Entity keys removed across the v1.1 and protocol-v2 migrations. The three
# moisture keys are retained: their entity identities now represent HA-side
# calibrated moisture instead of firmware-calculated moisture.
REMOVED_ENTITY_KEYS = frozenset(
    {
        "battery_low",
        "battery_measurement_fault",
        "battery_voltage",
        "ble_fault",
        "bottom_filtered_count",
        "bottom_range",
        "bottom_saturation",
        "calibration_invalid",
        "calibration_revision",
        "environmental_sensor_fault",
        "i2c_fault",
        "middle_filtered_count",
        "middle_range",
        "middle_saturation",
        "oscillator_configuration_fault",
        "status_word",
        "top_filtered_count",
        "top_range",
        "top_saturation",
        "tsc_acquisition_fault",
    }
)
