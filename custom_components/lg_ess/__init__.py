"""The LG ESS inverter integration."""

import logging

from pyess.aio_ess import ESS, ESSException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity_registry import async_migrate_entries

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LG ESS from config entry."""

    hass.data.setdefault(DOMAIN, {})

    try:
        ess = await ESS.create(None, entry.data["password"], entry.data["host"])
        hass.data[DOMAIN][entry.entry_id] = ess
    except ESSException as e:
        _LOGGER.exception("Error setting up ESS api")
        raise ConfigEntryNotReady from e

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        api = hass.data[DOMAIN].pop(entry.entry_id)
        await api.destruct()

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", entry.version)

    # Add serialno to unique id in order to allow multiple devices
    if entry.version == 1:
        ess = await ESS.create(None, entry.data[CONF_PASSWORD], entry.data[CONF_HOST])
        serialno = (await ess.get_systeminfo())["pms"]["serialno"]

        @callback
        def update_unique_id(entity_entry):
            """Update unique ID of entity entry."""
            return {"new_unique_id": serialno + "_" + entity_entry.unique_id}

        await async_migrate_entries(hass, entry.entry_id, update_unique_id)
        hass.config_entries.async_update_entry(entry, version=2)

    _LOGGER.info("Migration to version %s successful", entry.version)

    return True
