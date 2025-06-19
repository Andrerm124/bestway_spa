"""Config flow for Bestway Spa integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_APPID,
    CONF_APPSECRET,
    CONF_DEVICE_ID,
    CONF_PRODUCT_ID,
    CONF_REGISTRATION_ID,
    CONF_VISITOR_ID,
    CONF_CLIENT_ID,
)
from .spa import BestwaySpa

_LOGGER = logging.getLogger(__name__)

class BestwaySpaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bestway Spa."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                spa = BestwaySpa(
                    appid=user_input[CONF_APPID],
                    appsecret=user_input[CONF_APPSECRET],
                    device_id=user_input[CONF_DEVICE_ID],
                    product_id=user_input[CONF_PRODUCT_ID],
                    registration_id=user_input[CONF_REGISTRATION_ID],
                    visitor_id=user_input[CONF_VISITOR_ID],
                    client_id=user_input[CONF_CLIENT_ID],
                )
                await spa.get_state()
            except Exception as err:
                _LOGGER.error("Error connecting to Bestway Spa: %s", err)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="Bestway Spa",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_APPID): str,
                    vol.Required(CONF_APPSECRET): str,
                    vol.Required(CONF_DEVICE_ID): str,
                    vol.Required(CONF_PRODUCT_ID): str,
                    vol.Required(CONF_REGISTRATION_ID): str,
                    vol.Required(CONF_VISITOR_ID): str,
                    vol.Required(CONF_CLIENT_ID): str,
                }
            ),
            errors=errors,
        ) 