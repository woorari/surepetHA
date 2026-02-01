"""DataUpdateCoordinator for Sure Petcare."""
from __future__ import annotations

from datetime import timedelta
import logging

from surepy import SurePy
from surepy.exceptions import SurePetcareError

from homeassistant.components.persistent_notification import async_create
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER

class SurePetcareDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Sure Petcare data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: SurePy,
        household_id: int,
        update_interval: timedelta,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.api = api
        self.household_id = household_id
        self._notified_low_battery: set[int] = set()

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            # Fetch all data for the account
            data = await self.api.get_data()
            
            # Battery Notification Logic
            self._check_battery_levels(data)
            
            return data
        except SurePetcareError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def _check_battery_levels(self, data) -> None:
        """Check battery levels and notify if low."""
        for device_id, device in data.devices.items():
            # Only check devices in our household
            if device.household_id != self.household_id:
                continue

            # Check if device has a battery flag
            # Based on surepy 0.9.0 models, low_battery is a boolean on status
            low_battery = getattr(device.status, "low_battery", False)
            
            if low_battery and device_id not in self._notified_low_battery:
                async_create(
                    self.hass,
                    title="Sure Petcare Low Battery",
                    message=f"The battery in {device.name} is low.",
                    notification_id=f"{DOMAIN}_low_battery_{device_id}",
                )
                self._notified_low_battery.add(device_id)
            elif not low_battery and device_id in self._notified_low_battery:
                self._notified_low_battery.discard(device_id)
