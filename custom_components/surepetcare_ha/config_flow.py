"""Config flow for Sure Petcare integration."""
from __future__ import annotations

import logging
from typing import Any

from surepy import Surepy
from surepy.exceptions import SurePetcareAuthenticationError, SurePetcareConnectionError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_HOUSEHOLD_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    session = async_get_clientsession(hass)
    surepy = Surepy(
        data[CONF_EMAIL],
        data[CONF_PASSWORD],
        auth_token=None,
        api_timeout=10,
        session=session,
    )

    try:
        # Check credentials
        await surepy.auth()
    except SurePetcareAuthenticationError as err:
        _LOGGER.error("Authentication error: %s", err)
        # Check if it's 2FA (this is a bit speculative based on surepy 0.9.0)
        if "2fa" in str(err).lower() or "authorize" in str(err).lower():
            raise TwoFactorRequired from err
        raise InvalidAuth from err
    except SurePetcareConnectionError as err:
        raise CannotConnect from err

    households = await surepy.get_households()
    
    return {
        "surepy": surepy,
        "households": households,
    }

class SurePetcareConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sure Petcare."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._email: str | None = None
        self._password: str | None = None
        self._households: list[Any] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._email = user_input[CONF_EMAIL]
            self._password = user_input[CONF_PASSWORD]

            try:
                validated = await validate_input(self.hass, user_input)
                self._households = validated["households"]
                
                if not self._households:
                    return self.async_abort(reason="no_households")

                if len(self._households) == 1:
                    household = self._households[0]
                    self._household_id = household.id
                    self._household_name = household.name
                    return await self.async_step_discovery()

                return await self.async_step_household()

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except TwoFactorRequired:
                errors["base"] = "two_factor_required"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_household(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle household selection."""
        if user_input is not None:
            self._household_id = int(user_input[CONF_HOUSEHOLD_ID])
            self._household_name = next(
                h.name for h in self._households if h.id == self._household_id
            )
            return await self.async_step_discovery()

        household_options = {str(h.id): h.name for h in self._households}
        
        return self.async_show_form(
            step_id="household",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOUSEHOLD_ID): vol.In(household_options),
                }
            ),
        )

    async def async_step_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Display discovery summary."""
        if user_input is not None:
            return await self._async_create_entry()

        # Fetch discovery info
        session = async_get_clientsession(self.hass)
        surepy = Surepy(
            self._email,
            self._password,
            session=session,
        )
        
        # We need to get data for the summary
        data = await surepy.get_data()
        
        pet_names = [pet.name for pet in data.pets.values() if pet.household_id == self._household_id]
        device_names = [dev.name for dev in data.devices.values() if dev.household_id == self._household_id]

        summary = f"Pets: {', '.join(pet_names) if pet_names else 'None'}\n"
        summary += f"Devices: {', '.join(device_names) if device_names else 'None'}"

        return self.async_show_form(
            step_id="discovery",
            description_placeholders={"summary": summary},
        )

    async def _async_create_entry(self) -> FlowResult:
        """Create the config entry."""
        await self.async_set_unique_id(str(self._household_id))
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"Sure Petcare ({self._household_name})",
            data={
                CONF_EMAIL: self._email,
                CONF_PASSWORD: self._password,
                CONF_HOUSEHOLD_ID: self._household_id,
            },
        )

class CannotConnect(config_entries.HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(config_entries.HomeAssistantError):
    """Error to indicate there is invalid auth."""

class TwoFactorRequired(config_entries.HomeAssistantError):
    """Error to indicate 2FA is required."""
