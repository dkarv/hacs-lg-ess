"""Config flow for LG ESS integration."""
import logging
from typing import Any

from pyess.aio_ess import ESS, ESSAuthException, ESSException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _ess_schema(host: str | None = None):
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=host): str,
            vol.Required(CONF_PASSWORD): str,
        }
    )


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    await ESS.create(None, data[CONF_PASSWORD], data[CONF_HOST])

    # Return info that you want to store in the config entry.
    return {"title": "LG ESS"}


class EssConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LG ESS."""

    def __init__(self) -> None:
        """Initialize the ESS config flow."""
        self.discovery_schema: vol.Schema | None = None

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                # user_input['serialno'] = info['serialno']
                return self.async_create_entry(title=info["title"], data=user_input)
            except ESSAuthException:
                _LOGGER.exception("Wrong password")
                errors["base"] = "invalid_auth"
            except ESSException:
                _LOGGER.exception("Generic error setting up the ESS Api")
                errors["base"] = "unknown"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        data = self.discovery_schema or _ess_schema()
        return self.async_show_form(step_id="user", data_schema=data, errors=errors)

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle the zeroconf discovery."""
        host = discovery_info.host
        _LOGGER.info("Discovered device %s with %s", host, discovery_info)
        host = discovery_info.host
        data = {CONF_HOST: host}
        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured(updates=data)

        self._async_abort_entries_match(data)

        self.discovery_schema = _ess_schema(host)

        return await self.async_step_user()
