"""Constants for the Sure Petcare integration."""
from datetime import timedelta
import logging

DOMAIN = "surepetcare"
LOGGER = logging.getLogger(__package__)

PLATFORMS = ["sensor", "lock", "select", "device_tracker", "button"]

DEFAULT_POLLING_INTERVAL = timedelta(minutes=3)

CONF_HOUSEHOLD_ID = "household_id"
