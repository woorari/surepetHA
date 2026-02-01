"""Support for Sure Petcare buttons."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
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
    """Set up Sure Petcare button platform."""
    coordinator: SurePetcareDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[ButtonEntity] = []

    for pet_id, pet in coordinator.data.pets.items():
        if pet.household_id == coordinator.household_id:
            entities.append(SurePetcarePetButton(coordinator, pet_id, "inside"))
            entities.append(SurePetcarePetButton(coordinator, pet_id, "outside"))

    async_add_entities(entities)

class SurePetcarePetButton(CoordinatorEntity[SurePetcareDataUpdateCoordinator], ButtonEntity):
    """A pet location override button."""

    def __init__(
        self,
        coordinator: SurePetcareDataUpdateCoordinator,
        pet_id: int,
        location: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._pet_id = pet_id
        self._location = location
        pet = self.coordinator.data.pets[pet_id]
        
        self._attr_name = f"{pet.name} Mark {location.capitalize()}"
        self._attr_unique_id = f"pet_{pet_id}_mark_{location}"
        self._attr_icon = "mdi:home-import-outline" if location == "inside" else "mdi:home-export-outline"

    async def async_press(self) -> None:
        """Press the button."""
        # 1: Inside, 2: Outside
        location_id = 1 if self._location == "inside" else 2
        
        _LOGGER.debug("Setting pet %s location to %s", self._pet_id, location_id)
        
        try:
            # The plan specifies sac.set_pet_location
            await self.coordinator.api.sac.set_pet_location(self._pet_id, location_id)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error setting pet location for pet %s: %s", self._pet_id, err)

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"pet_{self._pet_id}")},
            "name": self.coordinator.data.pets[self._pet_id].name,
            "manufacturer": "Sure Petcare",
            "model": "Pet",
        }
