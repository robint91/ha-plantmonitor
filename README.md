# Plant Monitor BLE

A local-push Home Assistant custom integration for a battery-powered,
three-zone plant monitor. It passively decodes the monitor's 24-byte
manufacturer-specific Bluetooth advertisement. It never connects to the
device and performs no polling, writes, GATT operations, or cloud access.

## Installation

### HACS

1. In HACS, open **Integrations**, select the three-dot menu, and choose
   **Custom repositories**.
2. Add this repository URL with category **Integration**.
3. Search for **Plant Monitor BLE**, install it, and restart Home Assistant.

### Manual

Copy `custom_components/plant_monitor_ble` into the `custom_components`
directory under your Home Assistant configuration directory, then restart
Home Assistant.

## Setup and Bluetooth discovery

Enable Home Assistant's Bluetooth integration or a compatible passive
Bluetooth proxy. When a valid monitor frame is received, Home Assistant offers
the discovered device under **Settings > Devices & services**. Confirm the
discovery to create the entry. You can also choose **Add integration > Plant
Monitor BLE** and select one of the compatible devices currently in range.
Manual MAC-address entry is intentionally not supported.

Current firmware publishes a measurement every 30 seconds. The integration
marks entities unavailable after 90 seconds without a valid advertisement
(three missed reports); it never polls or actively scans the monitor. Repeated
copies of one packet are deduplicated by packet ID for 60 seconds per Bluetooth
address. Packet IDs are accepted again after that window.

Soil sensing uses a fixed TSC range code of `1`, corresponding to 11 nF, for
all three zones. Historical protocol-v1 frames with other range codes still
decode for backward compatibility, but range selection and range entities have
been removed.

## Entities

Enabled by default:

- Bottom, middle, and top soil moisture
- Air temperature
- Relative humidity
- Battery voltage in millivolts (diagnostic)
- Calibration invalid, battery low, and environmental-sensor fault problem
  binary sensors

Disabled by default diagnostics:

- Bottom, middle, and top filtered TSC counts
- Packet ID, calibration revision, hexadecimal status word, RSSI, and last
  received timestamp
- Bottom, middle, and top saturation; TSC acquisition; battery measurement;
  I2C; BLE; and oscillator/configuration fault binary sensors

The custom advertisement does **not** contain illuminance or battery
percentage. If the device also broadcasts standard BTHome, Home Assistant's
BTHome integration may independently expose those values and associate them
with the same Bluetooth device.

## Calibration

Current firmware stores one dry/wet calibration pair for each zone: bottom,
middle, and top. It performs the linear, clamped 0–100% conversion before
broadcasting. If a pair is invalid or unconfigured, the transmitted moisture
value is `0xFFFF`, which this integration exposes as unknown.

Home Assistant does not recalculate or reinterpret the transmitted moisture
value and does not write calibration to the monitor. Calibration must therefore
be configured in firmware using its supported tooling. Earlier releases of
this integration did not store HA-side calibration values, so there is no
calibration data to migrate; obsolete range diagnostic entities are removed
automatically when a version-1 config entry is migrated.

## Development Company Identifier

`0xFFFF` (65535) is a shared development Company Identifier, not a production
Bluetooth SIG assignment. The parser therefore performs strict length,
version, range-bit, and value-range validation before accepting a discovery.

When a production identifier is assigned, change all of the following in one
release:

1. `COMPANY_ID` in `custom_components/plant_monitor_ble/const.py`
2. `manufacturer_id` in `custom_components/plant_monitor_ble/manifest.json`
3. `COMPANY_ID` expectations and manufacturer-data fixtures in the tests

The 24-byte frame itself must still be stored as the manufacturer-data value;
the company identifier is the dictionary key and is not part of that value.

## Troubleshooting

- Wait at least 30 seconds for the next measurement. After 90 seconds without
  a valid frame, verify Bluetooth reception and device power.
- Confirm that Home Assistant's Bluetooth integration sees a local adapter or
  passive-capable proxy near the monitor.
- Improve receiver placement and check the disabled RSSI diagnostic sensor.
- A device using company ID `0xFFFF` is ignored unless the complete frame is
  exactly 24 bytes and passes all protocol checks. Malformed frames are dropped
  quietly; enable debug logging only when diagnosing reception.
- Invalid sensor sentinels appear as unknown, never as zero.

There is no YAML or runtime configuration. Calibration and all device commands
must be handled outside Home Assistant; this integration deliberately does not
support them or derive moisture from raw TSC counts.
