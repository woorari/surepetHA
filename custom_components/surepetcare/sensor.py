"""Support for Sure Petcare sensors."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SurePetcareDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sure Petcare sensors."""
    coordinator: SurePetcareDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    # Add sensors for devices
    for device_id, device in coordinator.data.devices.items():
        if device.household_id == coordinator.household_id:
            # Check if device has battery info (Hub usually doesn't, others do)
            if hasattr(device.status, "battery") or hasattr(device.status, "low_battery"):
                entities.append(SurePetcareBatterySensor(coordinator, device_id))
            
            entities.append(SurePetcareLastSeenSensor(coordinator, device_id, "device"))
            
            if getattr(device, "serial_number", None):
                entities.append(SurePetcareInfoSensor(coordinator, device_id, "serial"))
            
            if getattr(device, "product_id", None):
                entities.append(SurePetcareInfoSensor(coordinator, device_id, "product"))

            if hasattr(device.status, "curfew"):
                entities.append(SurePetcareCurfewSensor(coordinator, device_id))

    # Add sensors for pets
    for pet_id, pet in coordinator.data.pets.items():
        if pet.household_id == coordinator.household_id:
            entities.append(SurePetcareLastSeenSensor(coordinator, pet_id, "pet"))

    async_add_entities(entities)

class SurePetcareSensor(CoordinatorEntity[SurePetcareDataUpdateCoordinator], SensorEntity):
    """Base class for Sure Petcare sensors."""

    def __init__(
        self,
        coordinator: SurePetcareDataUpdateCoordinator,
        unique_id: int,
        identifier: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._unique_id = unique_id
        self._identifier = identifier

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._unique_id}_{self._identifier}"

class SurePetcareBatterySensor(SurePetcareSensor):
    """Sure Petcare battery sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: SurePetcareDataUpdateCoordinator, unique_id: int) -> None:
        """Initialize."""
        super().__init__(coordinator, unique_id, "battery")
        device = self.coordinator.data.devices[unique_id]
        self._attr_name = f"{device.name} Battery"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        device = self.coordinator.data.devices.get(self._unique_id)
        if not device:
            return None
        
        # Map binary flag to percentage as per requirement
        low_battery = getattr(device.status, "low_battery", False)
        return 10 if low_battery else 100

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device = self.coordinator.data.devices[self._unique_id]
        model = None
        if hasattr(device, "type"):
            model = getattr(device.type, "name", str(device.type)).replace("_", " ").title()
            
        return {
            "identifiers": {(DOMAIN, str(self._unique_id))},
            "name": device.name,
            "manufacturer": "Sure Petcare",
            "model": model,
        }

class SurePetcareLastSeenSensor(SurePetcareSensor):
    """Sure Petcare last seen sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: SurePetcareDataUpdateCoordinator, unique_id: int, target_type: str) -> None:
        """Initialize."""
        super().__init__(coordinator, unique_id, "last_seen")
        self._target_type = target_type
        if target_type == "pet":
            pet = self.coordinator.data.pets[unique_id]
            self._attr_name = f"{pet.name} Last Seen"
        else:
            device = self.coordinator.data.devices[unique_id]
            self._attr_name = f"{device.name} Last Seen"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self._target_type == "pet":
            entity = self.coordinator.data.pets.get(self._unique_id)
        else:
            entity = self.coordinator.data.devices.get(self._unique_id)
            
        if not entity:
            return None
            
        return getattr(entity.status, "since", None)

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        if self._target_type == "pet":
            pet = self.coordinator.data.pets[self._unique_id]
            return {
                "identifiers": {(DOMAIN, f"pet_{self._unique_id}")},
                "name": pet.name,
                "manufacturer": "Sure Petcare",
                "model": "Pet",
            }
        
        device = self.coordinator.data.devices[self._unique_id]
        model = None
        if hasattr(device, "type"):
            model = getattr(device.type, "name", str(device.type)).replace("_", " ").title()

        return {
            "identifiers": {(DOMAIN, str(self._unique_id))},
            "name": device.name,
            "manufacturer": "Sure Petcare",
            "model": model,
        }

class SurePetcareInfoSensor(SurePetcareSensor):
    """Sure Petcare information sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: SurePetcareDataUpdateCoordinator, unique_id: int, info_type: str) -> None:
        """Initialize."""
        super().__init__(coordinator, unique_id, info_type)
        self._info_type = info_type
        device = self.coordinator.data.devices[unique_id]
        if info_type == "serial":
            self._attr_name = f"{device.name} Serial Number"
        else:
            self._attr_name = f"{device.name} Product ID"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        device = self.coordinator.data.devices.get(self._unique_id)
        if not device:
            return None

        if self._info_type == "serial":
            return getattr(device, "serial_number", None)
        return getattr(device, "product_id", None)

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device = self.coordinator.data.devices[self._unique_id]
        model = None
        if hasattr(device, "type"):
            model = getattr(device.type, "name", str(device.type)).replace("_", " ").title()

        return {
            "identifiers": {(DOMAIN, str(self._unique_id))},
            "name": device.name,
            "manufacturer": "Sure Petcare",
            "model": model,
        }

class SurePetcareCurfewSensor(SurePetcareSensor):
    """Sure Petcare curfew sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:clock-check"

    def __init__(self, coordinator: SurePetcareDataUpdateCoordinator, unique_id: int) -> None:
        """Initialize."""
        super().__init__(coordinator, unique_id, "curfew")
        device = self.coordinator.data.devices[unique_id]
        self._attr_name = f"{device.name} Curfew Status"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        device = self.coordinator.data.devices.get(self._unique_id)
        if not device:
            return "Unknown"
        
        # Based on Sure Petcare API, curfew status is often in device.status.curfew
        # We check if any curfew is enabled.
        curfews = getattr(device.status, "curfew", [])
        
        # Handle both list and single object
        if isinstance(curfews, list):
            active = any(getattr(c, "enabled", False) for c in curfews)
        else:
            active = getattr(curfews, "enabled", False)
            
        return "Enabled" if active else "Disabled"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device = self.coordinator.data.devices[self._unique_id]
        model = None
        if hasattr(device, "type"):
            model = getattr(device.type, "name", str(device.type)).replace("_", " ").title()

        return {
            "identifiers": {(DOMAIN, str(self._unique_id))},
            "name": device.name,
            "manufacturer": "Sure Petcare",
            "model": model,
        }
