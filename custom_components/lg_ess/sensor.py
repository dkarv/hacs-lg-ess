"""Example integration using DataUpdateCoordinator."""

import logging

from pyess.aio_ess import ESSAuthException

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CommonCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from config entry."""
    ess = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = CommonCoordinator(hass, ess)

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    try:
        await coordinator.async_config_entry_first_refresh()
    except ESSAuthException as e:
        # Raising ConfigEntryAuthFailed will cancel future updates
        # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        raise ConfigEntryAuthFailed from e

    async_add_entities(
        [
            MeasurementSensor(coordinator, "BATT", "soc", PERCENTAGE),
            MeasurementSensor(coordinator, "BATT", "dc_power", UnitOfPower.WATT),
            MeasurementSensor(coordinator, "LOAD", "load_power", UnitOfPower.WATT),
            MeasurementSensor(coordinator, "PCS", "today_self_consumption", PERCENTAGE),
            IncreasingSensor(coordinator, "BATT", "today_batt_discharge_enery"),
            IncreasingSensor(coordinator, "BATT", "today_batt_charge_energy"),
            IncreasingSensor(coordinator, "BATT", "month_batt_discharge_energy"),
            IncreasingSensor(coordinator, "BATT", "month_batt_charge_energy"),
            IncreasingSensor(coordinator, "LOAD", "today_load_consumption_sum"),
            IncreasingSensor(coordinator, "LOAD", "today_pv_direct_consumption_enegy"),
            IncreasingSensor(coordinator, "LOAD", "today_grid_power_purchase_energy"),
            IncreasingSensor(coordinator, "LOAD", "month_load_consumption_sum"),
            IncreasingSensor(coordinator, "LOAD", "month_pv_direct_consumption_energy"),
            IncreasingSensor(coordinator, "LOAD", "month_grid_power_purchase_energy"),
            IncreasingSensor(coordinator, "PCS", "today_pv_generation_sum"),
            IncreasingSensor(coordinator, "PCS", "today_grid_feed_in_energy"),
            IncreasingSensor(coordinator, "PCS", "month_pv_generation_sum"),
            IncreasingSensor(coordinator, "PCS", "month_grid_feed_in_energy"),
        ]
    )


class EssSensor(CoordinatorEntity[CommonCoordinator], SensorEntity):
    """Basic sensor with common functionality."""

    _group: str
    _key: str

    def __init__(self, coordinator, group: str, key: str) -> None:
        """Initialize the sensor with the common coordinator."""
        super().__init__(coordinator)
        self._group = group
        self._key = key
        # Fix typos
        self._attr_translation_key = key.replace("_enery", "_energy").replace(
            "_enegy", "_energy"
        )
        self._attr_unique_id = self._attr_translation_key

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data[self._group][self._key]
        self.async_write_ha_state()


class MeasurementSensor(EssSensor):
    """Measurement sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, group: str, key: str, unit) -> None:
        """Initialize the sensor with the common coordinator."""
        super().__init__(coordinator, group, key)
        self._attr_native_unit_of_measurement = unit


class IncreasingSensor(EssSensor):
    """Increasing total sensor."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(
        self, coordinator, group: str, key: str, unit=UnitOfEnergy.WATT_HOUR
    ) -> None:
        """Initialize the sensor with the common coordinator."""
        super().__init__(coordinator, group, key)
        self._attr_native_unit_of_measurement = unit
