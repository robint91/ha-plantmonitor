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
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricPotential,
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
        key="bottom_moisture",
        translation_key="bottom_moisture",
        device_class=SensorDeviceClass.MOISTURE,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="middle_moisture",
        translation_key="middle_moisture",
        device_class=SensorDeviceClass.MOISTURE,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="top_moisture",
        translation_key="top_moisture",
        device_class=SensorDeviceClass.MOISTURE,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
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
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="bottom_filtered_count",
        translation_key="bottom_filtered_count",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="middle_filtered_count",
        translation_key="middle_filtered_count",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="top_filtered_count",
        translation_key="top_filtered_count",
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
        key="calibration_revision",
        translation_key="calibration_revision",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="status_word",
        translation_key="status_word",
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
        "bottom_moisture": update.bottom_moisture,
        "middle_moisture": update.middle_moisture,
        "top_moisture": update.top_moisture,
        "air_temperature": update.temperature_c,
        "relative_humidity": update.humidity,
        "battery_voltage": update.battery_mv,
        "bottom_filtered_count": update.bottom_filtered_count,
        "middle_filtered_count": update.middle_filtered_count,
        "top_filtered_count": update.top_filtered_count,
        "packet_id": update.packet_id,
        "calibration_revision": update.calibration_revision,
        "status_word": f"0x{update.status:04X}",
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
