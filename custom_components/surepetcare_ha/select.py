"""Support for Sure Petcare select entities."""
from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SurePetcareDataUpdateCoordinator

# Map indices to human-readable states as decided in Phase 1 Context
LOCK_STATE_MAP = {
    0: "Unlocked",
    1: "Locked (Can enter, cannot exit)",
    2: "Locked (Can exit, cannot enter)",
    3: "Locked (Total)",
}

# Reverse map for setting state
LOCK_STATE_REVERSE_MAP = {v: k for k, v in LOCK_STATE_MAP.items()}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sure Petcare select platform."""
    coordinator: SurePetcareDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SelectEntity] = []

    for device_id, device in coordinator.data.devices.items():
        if device.household_id == coordinator.household_id:
            if hasattr(device.status, "locking"):
                entities.append(SurePetcareSelect(coordinator, device_id))

    async_add_entities(entities)

class SurePetcareSelect(CoordinatorEntity[SurePetcareDataUpdateCoordinator], SelectEntity):
    """Sure Petcare lock state select entity."""

    _attr_options = list(LOCK_STATE_MAP.values())
    _attr_icon = "mdi:lock-cog"

    def __init__(self, coordinator: SurePetcareDataUpdateCoordinator, device_id: int) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        device = coordinator.data.devices[device_id]
        self._attr_name = f"{device.name} Lock Mode"
        self._attr_unique_id = f"{device_id}_lock_mode"

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        device = self.coordinator.data.devices.get(self._device_id)
        if not device or not hasattr(device.status, "locking"):
            return None
            
        locking_state = device.status.locking
        if not isinstance(locking_state, int):
            locking_state = getattr(locking_state, "value", locking_state)
            
        return LOCK_STATE_MAP.get(locking_state)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if (state_index := LOCK_STATE_REVERSE_MAP.get(option)) is not None:
            # Pessimistic update: Call API then refresh coordinator
            await self.coordinator.api.sac.set_lock_state(self._device_id, state_index)
            await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device = self.coordinator.data.devices[self._device_id]
        model = None
        if hasattr(device, "type"):
            model = getattr(device.type, "name", str(device.type)).replace("_", " ").title()

        return {
            "identifiers": {(DOMAIN, str(self._device_id))},
            "name": device.name,
            "manufacturer": "Sure Petcare",
            "model": model,
        }
