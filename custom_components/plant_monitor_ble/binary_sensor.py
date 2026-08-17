"""Binary sensor entities for Plant Monitor BLE."""

from typing import Final, override

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import NAME
from .coordinator import PlantMonitorBluetoothDataProcessor
from .types import PlantMonitorAdvertisement, PlantMonitorConfigEntry


def _problem_description(
    key: str, *, enabled: bool = False
) -> BinarySensorEntityDescription:
    return BinarySensorEntityDescription(
        key=key,
        translation_key=key,
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=enabled,
    )


BINARY_SENSOR_DESCRIPTIONS: Final = (
    _problem_description("calibration_invalid", enabled=True),
    _problem_description("battery_low", enabled=True),
    _problem_description("bottom_saturation"),
    _problem_description("middle_saturation"),
    _problem_description("top_saturation"),
    _problem_description("tsc_acquisition_fault"),
    _problem_description("environmental_sensor_fault", enabled=True),
    _problem_description("battery_measurement_fault"),
    _problem_description("i2c_fault"),
    _problem_description("ble_fault"),
    _problem_description("oscillator_configuration_fault"),
)


def _binary_values(update: PlantMonitorAdvertisement) -> dict[str, bool]:
    flags = update.flags
    return {
        "calibration_invalid": flags.calibration_invalid,
        "battery_low": flags.battery_low,
        "bottom_saturation": flags.bottom_saturation,
        "middle_saturation": flags.middle_saturation,
        "top_saturation": flags.top_saturation,
        "tsc_acquisition_fault": flags.tsc_acquisition_error,
        "environmental_sensor_fault": flags.hdc3022_error or flags.opt3001_error,
        "battery_measurement_fault": flags.battery_measurement_error,
        "i2c_fault": flags.i2c_error,
        "ble_fault": flags.ble_fault,
        "oscillator_configuration_fault": flags.oscillator_fault
        or flags.build_configuration_invalid,
    }


def binary_sensor_update_to_bluetooth_data_update(
    update: PlantMonitorAdvertisement | None,
) -> PassiveBluetoothDataUpdate[bool]:
    """Convert the latest decoded frame to binary sensor processor data."""
    if update is None:
        return PassiveBluetoothDataUpdate()
    values = _binary_values(update)
    return PassiveBluetoothDataUpdate(
        devices={None: DeviceInfo(name=NAME, manufacturer="Plant Monitor")},
        entity_descriptions={
            PassiveBluetoothEntityKey(description.key, None): description
            for description in BINARY_SENSOR_DESCRIPTIONS
        },
        entity_data={
            PassiveBluetoothEntityKey(key, None): value for key, value in values.items()
        },
        entity_names={},
    )


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: PlantMonitorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Plant Monitor BLE binary sensors."""
    processor = PlantMonitorBluetoothDataProcessor(
        binary_sensor_update_to_bluetooth_data_update
    )
    entry.async_on_unload(
        processor.async_add_entities_listener(
            PlantMonitorBluetoothBinarySensorEntity, async_add_entities
        )
    )
    entry.async_on_unload(
        entry.runtime_data.async_register_processor(
            processor, BinarySensorEntityDescription
        )
    )


class PlantMonitorBluetoothBinarySensorEntity(
    PassiveBluetoothProcessorEntity[PlantMonitorBluetoothDataProcessor[bool]],
    BinarySensorEntity,
):
    """A Plant Monitor BLE problem sensor."""

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the current problem state without performing I/O."""
        return self.processor.entity_data.get(self.entity_key)
