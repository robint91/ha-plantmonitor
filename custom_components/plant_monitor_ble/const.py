"""Constants for the Plant Monitor BLE integration."""

from datetime import timedelta

DOMAIN = "plant_monitor_ble"
NAME = "Plant Monitor BLE"
INTEGRATION_VERSION = "1.1.0"
CONFIG_ENTRY_VERSION = 2

# Development-only Bluetooth SIG Company Identifier. When a production identifier
# is assigned, update this value, manifest.json's manufacturer_id, and test vectors.
COMPANY_ID = 0xFFFF
PROTOCOL_VERSION = 1
FRAME_LENGTH = 24
DEDUPLICATION_WINDOW = timedelta(seconds=60)

EXPECTED_UPDATE_INTERVAL = timedelta(seconds=30)
# Allow three expected reports to be missed before marking entities unavailable.
STALE_TIMEOUT = timedelta(seconds=90)

FIXED_TSC_RANGE_CODE = 1
FIXED_TSC_CAPACITANCE_NF = 11

# Entity keys removed in v1.1 when firmware range selection was removed.
REMOVED_RANGE_ENTITY_KEYS = frozenset({"bottom_range", "middle_range", "top_range"})
