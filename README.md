# Plant Monitor BLE

A local-push Home Assistant custom integration for a battery-powered,
three-zone plant monitor. It passively decodes the monitor's protocol-v3
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
address. Packet IDs are accepted again after that window, including rollover
from 255 to 0.

## Entities

Enabled by default from the custom protocol:

- Air temperature
- Relative humidity
- Illuminance
- Bottom, middle, and top raw TSC counts from the fixed 100 nF sampling capacitor
- Bottom, middle, and top optional Home Assistant-calibrated soil moisture

The raw TSC entities have stable keys `bottom_tsc_count`, `middle_tsc_count`,
and `top_tsc_count`. They are unscaled integer counts with no percentage unit
or soil-moisture device class.

Packet ID, RSSI, and last-received timestamp are disabled by default diagnostic
entities.

Firmware also broadcasts standard BTHome temperature, relative humidity,
illuminance, battery percentage, and battery voltage measurements. BTHome
advertising is unchanged and remains owned by Home Assistant's BTHome
integration. The custom protocol-v3 packet has no battery fields and no
calibrated-moisture fields.

## Optional soil-moisture calibration

Protocol v3 carries only one raw 100 nF TSC count for each zone. The integration
can derive a separate soil-moisture percentage locally when independently
measured dry and wet counts are configured. This derived value is not decoded
from the custom packet and does not alter or relabel the raw TSC entities.

Open the integration's **Configure** dialog and enter `dry_count` and
`wet_count` for bottom, middle, and top. Each wet count must be lower than its
dry count. Until a complete valid calibration is saved, the corresponding
derived moisture entity is unavailable; a raw-count invalid sentinel makes
only that zone's raw and derived entities unavailable.

The charge-transfer count is inversely proportional to electrode capacitance,
so calibration interpolates the reciprocal count:

```text
moisture =
    100 * wet_count * (dry_count - count)
    / (count * (dry_count - wet_count))
```

The result is clamped to 0–100%. Zero counts and calibrations where
`dry_count <= wet_count` are invalid. Each zone is converted independently;
there is no overall or averaged moisture entity.

## Custom protocol v3

The complete manufacturer-specific AD element is exactly 19 bytes. All
multibyte values are little-endian.

| Advertisement offset | Size | Value |
| ---: | ---: | --- |
| 0 | 1 | AD length `0x12` |
| 1 | 1 | Manufacturer-specific AD type `0xFF` |
| 2 | 2 | Development company ID `0xFFFF`, little-endian |
| 4 | 15 | Manufacturer payload described below |

Home Assistant normally removes the company ID and exposes the final 15 bytes
as `manufacturer_data[0xFFFF]`. The integration requires exactly 15 bytes and
protocol version 3; truncated and trailing data are rejected.

| Payload offset | Size | Type | Field | Conversion / invalid value |
| ---: | ---: | --- | --- | --- |
| 0 | 1 | `uint8` | Protocol version | Must equal `3` |
| 1 | 1 | `uint8` | Packet ID | Rolls over from 255 to 0 |
| 2 | 2 | `uint16` | Bottom raw TSC | `0xFFFF` invalid |
| 4 | 2 | `uint16` | Middle raw TSC | `0xFFFF` invalid |
| 6 | 2 | `uint16` | Top raw TSC | `0xFFFF` invalid |
| 8 | 2 | `int16` | Temperature | Divide by 100 for °C; `0x8000` invalid |
| 10 | 2 | `uint16` | Relative humidity | Divide by 100 for %; `0xFFFF` invalid |
| 12 | 3 | `uint24` | Illuminance | Divide by 100 for lux; `0xFFFFFF` invalid |

Reference Home Assistant manufacturer payload:

```text
03 2A E8 03 D0 07 B8 0B 29 09 2E 16 39 30 00
```

Reference complete AD element:

```text
12 FF FF FF 03 2A E8 03 D0 07 B8 0B 29 09 2E 16 39 30 00
```

It decodes to packet ID 42; bottom/middle/top raw TSC counts
1000/2000/3000; 23.45 °C; 56.78%; and 123.45 lux.

Protocol v2 advertisements are no longer parsed. Existing config entries are
migrated in place, their obsolete range-specific entity-registry entries are
removed, and the three stable generic raw-count entity keys are retained.

## Development Company Identifier

`0xFFFF` (65535) is a shared development Company Identifier, not a production
Bluetooth SIG assignment. When a production identifier is assigned, change
all of the following in one release:

1. `COMPANY_ID` in `custom_components/plant_monitor_ble/const.py`
2. `manufacturer_id` in `custom_components/plant_monitor_ble/manifest.json`
3. Company-ID expectations and manufacturer-data fixtures in the tests

The 15-byte payload remains the manufacturer-data value; the company ID is the
dictionary key and is not part of that value.

## Troubleshooting

- Wait at least 30 seconds for the next measurement. After 90 seconds without
  a valid frame, verify Bluetooth reception and device power.
- Confirm that Home Assistant's Bluetooth integration sees a local adapter or
  passive-capable proxy near the monitor.
- Improve receiver placement and check the disabled RSSI diagnostic sensor.
- A device using company ID `0xFFFF` is ignored unless its manufacturer payload
  is exactly 15 bytes, starts with protocol version 3, and passes value checks.
- Invalid sensor sentinels appear as unknown, never as zero.
