"""Support for Sure Petcare pet tracking."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SurePetcareDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sure Petcare device tracker platform."""
    coordinator: SurePetcareDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SurePetcarePetTracker] = []

    for pet_id, pet in coordinator.data.pets.items():
        if pet.household_id == coordinator.household_id:
            entities.append(SurePetcarePetTracker(coordinator, pet_id))

    async_add_entities(entities)

class SurePetcarePetTracker(CoordinatorEntity[SurePetcareDataUpdateCoordinator], TrackerEntity):
    """A pet device tracker."""

    def __init__(self, coordinator: SurePetcareDataUpdateCoordinator, pet_id: int) -> None:
        """Initialize the tracker."""
        super().__init__(coordinator)
        self._pet_id = pet_id
        pet = self.coordinator.data.pets[pet_id]
        self._attr_name = pet.name
        self._attr_unique_id = f"pet_{pet_id}_tracker"

    @property
    def pet(self):
        """Return the pet object."""
        return self.coordinator.data.pets.get(self._pet_id)

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS

    @property
    def location_name(self) -> str:
        """Return a location name for the current location of the device."""
        if not self.pet:
            return "Unknown"

        # Map Sure Petcare location IDs: 1: Inside, 2: Outside, 0: Unknown
        location_id = getattr(self.pet.location, "where", 0)
        
        if location_id == 1:
            return "Inside"
        if location_id == 2:
            return "Away"
            
        return "Unknown"

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return None

    @property
    def entity_picture(self) -> str | None:
        """Return the pet's photo if available."""
        if not self.pet:
            return None
        return getattr(self.pet, "photo_url", None)

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        if self.location_name == "Unknown":
            return "mdi:alert-circle-outline"
            
        if not self.pet:
            return "mdi:help-circle-outline"
            
        species = getattr(self.pet, "species_name", "").lower()
        if "cat" in species:
            return "mdi:cat"
        if "dog" in species:
            return "mdi:dog"
            
        return "mdi:pet-theory"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {}
        if self.pet:
            attrs["pet_id"] = self._pet_id
            attrs["location_since"] = getattr(self.pet.location, "since", None)
            
            # Map location ID for reference
            location_id = getattr(self.pet.location, "where", 0)
            attrs["location_id"] = location_id
            
        return attrs

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"pet_{self._pet_id}")},
            "name": self._attr_name,
            "manufacturer": "Sure Petcare",
            "model": "Pet",
        }
