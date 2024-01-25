"""The LG ESS inverter integration."""

import logging

from pyess.aio_ess import ESS, ESSException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LG ESS from config entry."""

    hass.data.setdefault(DOMAIN, {})

    try:
        ess = await ESS.create("LG_ESS", entry.data["password"], entry.data["host"])
        hass.data[DOMAIN][entry.entry_id] = ess
    except ESSException as e:
        _LOGGER.exception("Error setting up ESS api")
        await ess.destruct()
        raise ConfigEntryNotReady from e

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        api = hass.data[DOMAIN].pop(entry.entry_id)
        await api.destruct()

    return unload_ok
