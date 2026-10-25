from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfDataRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TransmissionConfigEntry
from .const import DOMAIN
from .coordinator import TransmissionCoordinator, TransmissionData


@dataclass(frozen=True, kw_only=True)
class TransmissionSensorDescription(SensorEntityDescription):
    value_fn: Callable[[TransmissionData], int]


SENSORS: tuple[TransmissionSensorDescription, ...] = (
    TransmissionSensorDescription(
        key="download_speed",
        translation_key="download_speed",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: d.download_speed,
    ),
    TransmissionSensorDescription(
        key="upload_speed",
        translation_key="upload_speed",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: d.upload_speed,
    ),
    TransmissionSensorDescription(
        key="active_torrents",
        translation_key="active_torrents",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.active_torrents,
    ),
    TransmissionSensorDescription(
        key="paused_torrents",
        translation_key="paused_torrents",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.paused_torrents,
    ),
    TransmissionSensorDescription(
        key="total_torrents",
        translation_key="total_torrents",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.total_torrents,
    ),
    TransmissionSensorDescription(
        key="downloading",
        translation_key="downloading",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.downloading,
    ),
    TransmissionSensorDescription(
        key="seeding",
        translation_key="seeding",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.seeding,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TransmissionConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        TransmissionSensor(coordinator, entry.entry_id, desc) for desc in SENSORS
    )


class TransmissionSensor(CoordinatorEntity[TransmissionCoordinator], SensorEntity):
    _attr_has_entity_name = True
    entity_description: TransmissionSensorDescription

    def __init__(
        self,
        coordinator: TransmissionCoordinator,
        entry_id: str,
        description: TransmissionSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Transmission",
            manufacturer="Transmission",
        )

    @property
    def native_value(self) -> int:
        return self.entity_description.value_fn(self.coordinator.data)
