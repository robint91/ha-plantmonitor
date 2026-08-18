# Plant Monitor BLE

A local-push Home Assistant custom integration for a battery-powered,
three-zone plant monitor. It passively decodes the monitor's protocol-v2
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
- Bottom, middle, and top raw TSC count from the fixed 11 nF measurement
- Bottom, middle, and top calibrated soil moisture

Disabled by default diagnostics:

- Bottom, middle, and top TSC counts at 1 nF, 11 nF, and 48 nF (nine entities)
- Packet ID, RSSI, and last received timestamp

The generic fixed-measurement raw entity keys are `bottom_tsc_count`,
`middle_tsc_count`, and `top_tsc_count`. The stable diagnostic TSC entity keys
include both zone and capacitor range:
`bottom_tsc_1nf`, `bottom_tsc_11nf`, `bottom_tsc_48nf`,
`middle_tsc_1nf`, `middle_tsc_11nf`, `middle_tsc_48nf`, `top_tsc_1nf`,
`top_tsc_11nf`, and `top_tsc_48nf`.

Firmware also broadcasts standard BTHome temperature, relative humidity,
illuminance, battery percentage, and battery voltage measurements. Battery
entities are owned by Home Assistant's BTHome integration only; the custom
packet has no battery fields. BTHome does not publish soil moisture, and this
integration does not expect or create a BTHome moisture entity.

## Soil-moisture calibration

Protocol v2 moves soil calibration entirely out of firmware. The custom packet
contains raw TSC counts and never contains firmware-calibrated moisture,
calibration constants, or a calibration revision.

The firmware's TSC sampling-capacitor/gain configuration is fixed at 11 nF.
There is no auto-ranging or range correction. The three generic raw-count
entities and the calibration calculation therefore use the 11 nF reading for
their zone. All nine range-specific raw TSC measurements remain available as
diagnostic sensors and are never replaced or averaged.

Open the integration's **Configure** dialog and enter an independently measured
`dry_count` and `wet_count` for bottom, middle, and top. Each wet count must be
lower than its dry count. Until a complete valid calibration is saved, the
corresponding moisture entity is unavailable; a raw count invalid sentinel also
makes only that zone's moisture unavailable.

The charge-transfer count is inversely proportional to electrode capacitance,
so calibration interpolates the reciprocal count rather than the count itself:

```text
moisture =
    100 * wet_count * (dry_count - count)
    / (count * (dry_count - wet_count))
```

The result is clamped to 0–100%. A count at or above the dry point is 0%; a
count at or below the wet point is 100%. Zero counts and calibrations where
`dry_count <= wet_count` are invalid. Each zone is converted independently.
The integration does not publish an overall/averaged moisture entity.

## Custom protocol v2

The firmware emits one 31-byte advertisement consisting only of a
manufacturer-specific AD element; it intentionally has no Flags AD element.
All multibyte values are little-endian.

| Advertisement byte | Size | Value |
| ---: | ---: | --- |
| 0 | 1 | AD length `0x1E` (30 following bytes) |
| 1 | 1 | Manufacturer-specific AD type `0xFF` |
| 2 | 2 | Development company ID `0xFFFF`, little-endian |
| 4 | 27 | Manufacturer payload described below |

Home Assistant normally removes the company ID and exposes the final 27 bytes
as `manufacturer_data[0xFFFF]`. The integration rejects values shorter than 27
bytes and protocol versions other than 2. If a Bluetooth stack supplies bytes
after the complete payload, only the documented first 27 bytes are decoded.

| Payload offset | Size | Field | Conversion / invalid value |
| ---: | ---: | --- | --- |
| 0 | 1 | Protocol version | Must equal `2` |
| 1 | 1 | Packet ID | Unsigned; rolls over from 255 to 0 |
| 2 | 2 | Bottom TSC, 1 nF | `0xFFFF` invalid |
| 4 | 2 | Bottom TSC, 11 nF | `0xFFFF` invalid |
| 6 | 2 | Bottom TSC, 48 nF | `0xFFFF` invalid |
| 8 | 2 | Middle TSC, 1 nF | `0xFFFF` invalid |
| 10 | 2 | Middle TSC, 11 nF | `0xFFFF` invalid |
| 12 | 2 | Middle TSC, 48 nF | `0xFFFF` invalid |
| 14 | 2 | Top TSC, 1 nF | `0xFFFF` invalid |
| 16 | 2 | Top TSC, 11 nF | `0xFFFF` invalid |
| 18 | 2 | Top TSC, 48 nF | `0xFFFF` invalid |
| 20 | 2 | Signed temperature | `int16 / 100` °C; `0x8000` invalid |
| 22 | 2 | Relative humidity | `uint16 / 100` %; `0xFFFF` invalid |
| 24 | 3 | Illuminance | `uint24 / 100` lux; `0xFFFFFF` invalid |

The reference manufacturer payload is:

```text
02 2A
E8 03 4C 04 B0 04
D0 07 34 08 98 08
B8 0B 1C 0C 80 0C
29 09
2E 16
39 30 00
```

It decodes to packet ID 42; bottom TSC 1000/1100/1200; middle TSC
2000/2100/2200; top TSC 3000/3100/3200; 23.45 °C; 56.78%; and 123.45 lux.

## Development Company Identifier

`0xFFFF` (65535) is a shared development Company Identifier, not a production
Bluetooth SIG assignment. When a production identifier is assigned, change
all of the following in one release:

1. `COMPANY_ID` in `custom_components/plant_monitor_ble/const.py`
2. `manufacturer_id` in `custom_components/plant_monitor_ble/manifest.json`
3. Company-ID expectations and manufacturer-data fixtures in the tests

The 27-byte payload must remain the manufacturer-data value; the company ID is
the dictionary key and is not part of that value.

## Troubleshooting

- Wait at least 30 seconds for the next measurement. After 90 seconds without
  a valid frame, verify Bluetooth reception and device power.
- Confirm that Home Assistant's Bluetooth integration sees a local adapter or
  passive-capable proxy near the monitor.
- Improve receiver placement and check the disabled RSSI diagnostic sensor.
- A device using company ID `0xFFFF` is ignored unless its manufacturer payload
  is at least 27 bytes, starts with protocol version 2, and passes value checks.
- Invalid sensor sentinels appear as unknown, never as zero.
