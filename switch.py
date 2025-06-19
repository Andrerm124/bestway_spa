"""Switch entities for Bestway Spa."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Bestway Spa switch entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    spa = hass.data[DOMAIN][entry.entry_id]["spa"]

    async_add_entities(
        [
            BestwaySpaPower(coordinator, spa),
            BestwaySpaFilter(coordinator, spa),
            BestwaySpaWave(coordinator, spa),
        ]
    )

class BestwaySpaSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Bestway Spa switch."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        spa: Any,
        name: str,
        state_key: str,
        unique_id: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._spa = spa
        self._state_key = state_key
        self._attr_name = name
        self._attr_unique_id = unique_id

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        if not self.coordinator.data:
            _LOGGER.debug("No coordinator data available for %s", self._attr_name)
            return False
        state_value = self.coordinator.data.get(self._state_key, 0)
        # Any non-zero value means the switch is on
        state = state_value != 0
        _LOGGER.debug("%s state: %s (raw value: %s)", self._attr_name, state, state_value)
        return state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        _LOGGER.debug("Turning on %s", self._attr_name)
        # First update the API
        await self._spa.set_state(self._state_key, 1)
        # Optimistically update our local state
        self.coordinator.data[self._state_key] = 1
        self.async_write_ha_state()
        # Wait 5 seconds before refreshing
        await asyncio.sleep(5)
        # Then refresh the full state
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        _LOGGER.debug("Turning off %s", self._attr_name)
        # First update the API
        await self._spa.set_state(self._state_key, 0)
        # Optimistically update our local state
        self.coordinator.data[self._state_key] = 0
        self.async_write_ha_state()
        # Wait 5 seconds before refreshing
        await asyncio.sleep(5)
        # Then refresh the full state
        await self.coordinator.async_request_refresh()

class BestwaySpaPower(BestwaySpaSwitch):
    """Representation of the Bestway Spa power switch."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        spa: Any,
    ) -> None:
        """Initialize the power switch."""
        super().__init__(
            coordinator,
            spa,
            "Bestway Spa Power",
            "power_state",
            f"{spa._device_id}_power",
        )

class BestwaySpaFilter(BestwaySpaSwitch):
    """Representation of the Bestway Spa filter switch."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        spa: Any,
    ) -> None:
        """Initialize the filter switch."""
        super().__init__(
            coordinator,
            spa,
            "Bestway Spa Filter",
            "filter_state",
            f"{spa._device_id}_filter",
        )

class BestwaySpaWave(BestwaySpaSwitch):
    """Representation of the Bestway Spa wave switch."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        spa: Any,
    ) -> None:
        """Initialize the wave switch."""
        super().__init__(
            coordinator,
            spa,
            "Bestway Spa Wave",
            "wave_state",
            f"{spa._device_id}_wave",
        ) 