"""The Sure Petcare integration."""
from __future__ import annotations

import logging

from surepy import SurePy
from surepy.exceptions import SurePetcareAuthenticationError, SurePetcareConnectionError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_HOUSEHOLD_ID, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sure Petcare from a config entry."""
    
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    household_id = entry.data[CONF_HOUSEHOLD_ID]

    session = async_get_clientsession(hass)
    surepy = SurePy(
        email,
        password,
        auth_token=None,
        api_timeout=10,
        session=session,
    )

    try:
        # Validate credentials and get initial data
        await surepy.get_token()
    except SurePetcareAuthenticationError as err:
        raise ConfigEntryAuthFailed from err
    except SurePetcareConnectionError as err:
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": surepy,
        "household_id": household_id,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
