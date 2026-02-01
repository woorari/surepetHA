"""Support for Sure Petcare locks."""
from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
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
    """Set up Sure Petcare locks."""
    coordinator: SurePetcareDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SurePetcareLock] = []

    for device_id, device in coordinator.data.devices.items():
        if device.household_id == coordinator.household_id:
            if hasattr(device.status, "locking"):
                entities.append(SurePetcareLock(coordinator, device_id))

    async_add_entities(entities)

class SurePetcareLock(CoordinatorEntity[SurePetcareDataUpdateCoordinator], LockEntity):
    """Sure Petcare lock entity."""

    def __init__(self, coordinator: SurePetcareDataUpdateCoordinator, device_id: int) -> None:
        """Initialize the lock."""
        super().__init__(coordinator)
        self._device_id = device_id
        device = coordinator.data.devices[device_id]
        self._attr_name = f"{device.name} Exit Lock"
        self._attr_unique_id = f"{device_id}_lock"

    @property
    def is_locked(self) -> bool:
        """Return true if locked."""
        device = self.coordinator.data.devices.get(self._device_id)
        if not device or not hasattr(device.status, "locking"):
            return False
        
        # Sure Petcare lock states:
        # 0: Unlocked
        # 1: Locked In
        # 2: Locked Out
        # 3: Locked All
        # Mapping: locked_in (1) or locked_all (3) counts as "locked" for this entity
        # Based on surepy, locking can be an int or a LockState enum
        locking_state = device.status.locking
        if not isinstance(locking_state, int):
            locking_state = getattr(locking_state, "value", locking_state)
            
        return locking_state in [1, 3]

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the flap."""
        # We map "lock" to "Locked In" (cannot exit)
        # 1 = LOCKED_IN
        await self.coordinator.api.sac.set_lock_state(self._device_id, 1)
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the flap."""
        # 0 = UNLOCKED
        await self.coordinator.api.sac.set_lock_state(self._device_id, 0)
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
