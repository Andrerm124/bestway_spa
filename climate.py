"""Climate entity for Bestway Spa."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_WHOLE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
    MIN_TEMP,
    MAX_TEMP,
    HEATER_STATE_OFF,
    HEATER_STATE_HEATING,
    HEATER_STATE_PASSIVE,
)
from .spa import BestwaySpa

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Bestway Spa climate entity."""
    spa: BestwaySpa = hass.data[DOMAIN][entry.entry_id]["spa"]
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([BestwaySpaClimate(spa, coordinator)])

class BestwaySpaClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Bestway Spa climate entity."""

    def __init__(
        self,
        spa: BestwaySpa,
        coordinator: DataUpdateCoordinator,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._spa = spa
        self._attr_name = "Bestway Spa"
        self._attr_unique_id = f"{spa._device_id}_climate"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_precision = PRECISION_WHOLE
        self._attr_target_temperature_step = 1
        self._attr_min_temp = MIN_TEMP
        self._attr_max_temp = MAX_TEMP
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        if not self.coordinator.data:
            return None
        return float(self.coordinator.data.get("water_temperature", 0))

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the target temperature."""
        if not self.coordinator.data:
            return None
        return float(self.coordinator.data.get("temperature_setting", 0))

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        if not self.coordinator.data:
            return HVACMode.OFF
        
        heater_state = self.coordinator.data.get("heater_state", 0)
        return HVACMode.HEAT if heater_state != 0 else HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current HVAC action."""
        if not self.coordinator.data:
            return HVACAction.OFF
        
        heater_state = self.coordinator.data.get("heater_state", 0)
        if heater_state == HEATER_STATE_HEATING:
            return HVACAction.HEATING
        elif heater_state == HEATER_STATE_PASSIVE:
            return HVACAction.IDLE
        return HVACAction.OFF

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity specific state attributes."""
        if not self.coordinator.data:
            return {"mode": "off", "error_code": None}
        
        # Get error code if present
        error_code = self.coordinator.data.get("error_code")
        _LOGGER.debug("Error code from response: %s", error_code)
        
        # Get heater state
        heater_state = self.coordinator.data.get("heater_state", 0)
        _LOGGER.debug("Current heater state: %s", heater_state)
        
        if heater_state == HEATER_STATE_HEATING:
            mode = "heating"
        elif heater_state == HEATER_STATE_PASSIVE:
            mode = "idle"
        else:
            mode = "off"
            
        _LOGGER.debug("Setting mode attribute to: %s", mode)
        return {
            "mode": mode,
            "error_code": error_code
        }

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            await self._spa.set_state("temperature_setting", int(kwargs[ATTR_TEMPERATURE]))
            # Optimistically update our local state
            self.coordinator.data["temperature_setting"] = int(kwargs[ATTR_TEMPERATURE])
            self.async_write_ha_state()
            # Wait 5 seconds before refreshing
            await asyncio.sleep(5)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode."""
        if hvac_mode == HVACMode.HEAT:
            await self._spa.set_state("heater_state", HEATER_STATE_HEATING)
            # Optimistically update our local state
            self.coordinator.data["heater_state"] = HEATER_STATE_HEATING
        else:
            await self._spa.set_state("heater_state", HEATER_STATE_OFF)
            # Optimistically update our local state
            self.coordinator.data["heater_state"] = HEATER_STATE_OFF
        self.async_write_ha_state()
        # Wait 5 seconds before refreshing
        await asyncio.sleep(5)
        await self.coordinator.async_request_refresh() 