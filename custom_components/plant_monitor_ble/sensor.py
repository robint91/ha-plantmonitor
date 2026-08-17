"""Sensor entities for Plant Monitor BLE."""

from datetime import datetime
from typing import Any, Final, override

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    LIGHT_LUX,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import NAME
from .coordinator import PlantMonitorBluetoothDataProcessor
from .types import PlantMonitorAdvertisement, PlantMonitorConfigEntry

SENSOR_DESCRIPTIONS: Final = (
    SensorEntityDescription(
        key="air_temperature",
        translation_key="air_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="relative_humidity",
        translation_key="relative_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="illuminance",
        translation_key="illuminance",
        device_class=SensorDeviceClass.ILLUMINANCE,
        native_unit_of_measurement=LIGHT_LUX,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="bottom_tsc_1nf",
        translation_key="bottom_tsc_1nf",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="bottom_tsc_11nf",
        translation_key="bottom_tsc_11nf",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="bottom_tsc_48nf",
        translation_key="bottom_tsc_48nf",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="middle_tsc_1nf",
        translation_key="middle_tsc_1nf",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="middle_tsc_11nf",
        translation_key="middle_tsc_11nf",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="middle_tsc_48nf",
        translation_key="middle_tsc_48nf",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="top_tsc_1nf",
        translation_key="top_tsc_1nf",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="top_tsc_11nf",
        translation_key="top_tsc_11nf",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="top_tsc_48nf",
        translation_key="top_tsc_48nf",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="packet_id",
        translation_key="packet_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="rssi",
        translation_key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="last_received",
        translation_key="last_received",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


def _sensor_values(
    update: PlantMonitorAdvertisement,
) -> dict[str, int | float | str | datetime | None]:
    return {
        "air_temperature": update.temperature_c,
        "relative_humidity": update.humidity,
        "illuminance": update.illuminance_lux,
        "bottom_tsc_1nf": update.bottom_tsc_1nf,
        "bottom_tsc_11nf": update.bottom_tsc_11nf,
        "bottom_tsc_48nf": update.bottom_tsc_48nf,
        "middle_tsc_1nf": update.middle_tsc_1nf,
        "middle_tsc_11nf": update.middle_tsc_11nf,
        "middle_tsc_48nf": update.middle_tsc_48nf,
        "top_tsc_1nf": update.top_tsc_1nf,
        "top_tsc_11nf": update.top_tsc_11nf,
        "top_tsc_48nf": update.top_tsc_48nf,
        "packet_id": update.packet_id,
        "rssi": update.rssi,
        "last_received": update.received_at,
    }


def sensor_update_to_bluetooth_data_update(
    update: PlantMonitorAdvertisement | None,
) -> PassiveBluetoothDataUpdate[Any]:
    """Convert the latest decoded frame to sensor processor data."""
    if update is None:
        return PassiveBluetoothDataUpdate()
    values = _sensor_values(update)
    return PassiveBluetoothDataUpdate(
        devices={None: DeviceInfo(name=NAME, manufacturer="Plant Monitor")},
        entity_descriptions={
            PassiveBluetoothEntityKey(description.key, None): description
            for description in SENSOR_DESCRIPTIONS
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
    """Set up Plant Monitor BLE sensors."""
    processor = PlantMonitorBluetoothDataProcessor(
        sensor_update_to_bluetooth_data_update
    )
    entry.async_on_unload(
        processor.async_add_entities_listener(
            PlantMonitorBluetoothSensorEntity, async_add_entities
        )
    )
    entry.async_on_unload(
        entry.runtime_data.async_register_processor(processor, SensorEntityDescription)
    )


class PlantMonitorBluetoothSensorEntity(
    PassiveBluetoothProcessorEntity[PlantMonitorBluetoothDataProcessor[Any]],
    SensorEntity,
):
    """A Plant Monitor BLE sensor."""

    @property
    @override
    def native_value(self) -> Any:
        """Return the current native value without performing I/O."""
        return self.processor.entity_data.get(self.entity_key)
