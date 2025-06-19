"""The Bestway Spa integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

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

PLATFORMS = ["climate", "switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bestway Spa from a config entry."""
    spa = BestwaySpa(
        appid=entry.data[CONF_APPID],
        appsecret=entry.data[CONF_APPSECRET],
        device_id=entry.data[CONF_DEVICE_ID],
        product_id=entry.data[CONF_PRODUCT_ID],
        registration_id=entry.data[CONF_REGISTRATION_ID],
        visitor_id=entry.data[CONF_VISITOR_ID],
        client_id=entry.data[CONF_CLIENT_ID],
    )

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Bestway Spa",
        update_method=spa.get_state,
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "spa": spa,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok 