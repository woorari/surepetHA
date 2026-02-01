"""The Sure Petcare integration."""
from __future__ import annotations

import logging

from surepy import Surepy
from surepy.exceptions import SurePetcareAuthenticationError, SurePetcareConnectionError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_HOUSEHOLD_ID, DEFAULT_POLLING_INTERVAL, DOMAIN, PLATFORMS
from .coordinator import SurePetcareDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sure Petcare from a config entry."""
    
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    household_id = entry.data[CONF_HOUSEHOLD_ID]

    session = async_get_clientsession(hass)
    surepy = Surepy(
        email,
        password,
        auth_token=None,
        api_timeout=10,
        session=session,
    )

    try:
        # Validate credentials
        await surepy.get_token()
    except SurePetcareAuthenticationError as err:
        raise ConfigEntryAuthFailed from err
    except SurePetcareConnectionError as err:
        raise ConfigEntryNotReady from err

    coordinator = SurePetcareDataUpdateCoordinator(
        hass,
        surepy,
        household_id,
        DEFAULT_POLLING_INTERVAL,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    async def handle_set_pet_location(call) -> None:
        """Handle the service call."""
        pet_id = call.data["pet_id"]
        location_id = int(call.data["location"])

        # Find the coordinator that has this pet
        for coord in hass.data[DOMAIN].values():
            if pet_id in coord.data.pets:
                try:
                    await coord.api.sac.set_pet_location(pet_id, location_id)
                    await coord.async_request_refresh()
                    return
                except Exception as err:
                    _LOGGER.error("Error setting pet location via service: %s", err)
                    break

    if not hass.services.has_service(DOMAIN, "set_pet_location"):
        hass.services.async_register(DOMAIN, "set_pet_location", handle_set_pet_location)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
