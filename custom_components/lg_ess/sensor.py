"""Example integration using DataUpdateCoordinator."""

from datetime import date, datetime
import logging

from pyess.aio_ess import ESSAuthException

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import (
    CommonCoordinator,
    ESSCoordinator,
    HomeCoordinator,
    SystemInfoCoordinator,
)

_LOGGER = logging.getLogger(__name__)

_WINTER = "mdi:snowflake"
_CHARGING = "mdi:battery-plus"
_DISCHARGING = "mdi:battery-minus"
_EV = "mdi:ev-station"
_BACKUP = "mdi:battery-lock"
_GRID = "mdi:transmission-tower"
_TOGRID = "mdi:transmission-tower-export"
_FROMGRID = "mdi:transmission-tower-import"
_ONE = "mdi:numeric-1-box"
_TWO = "mdi:numeric-2-box"
_THREE = "mdi:numeric-3-box"
_BATTERYSTATUS = "mdi:battery-check"
_BATTERYHALF = "mdi:battery-50"
_BATTERYHOME = "mdi:home-battery"
_BATTERYLOAD = "mdi:battery-charging"
_PV = "mdi:solar-power"
_CO2 = "mdi:molecule-co2"
_LOAD = "mdi:home-lightning-bolt"
_HEATPUMP = "mdi:heat-pump"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from config entry."""
    ess = hass.data[DOMAIN][config_entry.entry_id]
    common_coordinator = CommonCoordinator(hass, ess)
    system_coordinator = SystemInfoCoordinator(hass, ess)
    home_coordinator = HomeCoordinator(hass, ess)

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    try:
        await common_coordinator.async_config_entry_first_refresh()
        await system_coordinator.async_config_entry_first_refresh()
        await home_coordinator.async_config_entry_first_refresh()
    except ESSAuthException as e:
        # Raising ConfigEntryAuthFailed will cancel future updates
        # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        raise ConfigEntryAuthFailed from e

    async_add_entities(
        [
            MeasurementSensor(
                common_coordinator,
                "BATT",
                "dc_power",
                UnitOfPower.WATT,
                icon=_BATTERYLOAD,
            ),
            MeasurementSensor(
                common_coordinator, "LOAD", "load_power", UnitOfPower.WATT, icon=_LOAD
            ),
            MeasurementSensor(
                common_coordinator, "PCS", "today_self_consumption", PERCENTAGE
            ),
            EssSensor(system_coordinator, "pms", "model"),
            EssSensor(system_coordinator, "pms", "serialno"),
            EssSensor(system_coordinator, "pms", "ac_input_power"),  # number
            EssSensor(system_coordinator, "pms", "ac_output_power"),  # number
            EssSensor(system_coordinator, "pms", "install_date", _parse_date),
            MeasurementSensor(
                system_coordinator,
                "batt",
                "capacity",
                UnitOfEnergy.WATT_HOUR,
                lambda x: int(x) * 100,
            ),
            EssSensor(system_coordinator, "batt", "type"),  #
            MeasurementSensor(
                system_coordinator, "batt", "hbc_cycle_count_1"
            ),  # number
            MeasurementSensor(
                system_coordinator, "batt", "hbc_cycle_count_2"
            ),  # number
            EssSensor(system_coordinator, "batt", "install_date", _parse_date),
            EssSensor(system_coordinator, "version", "pms_version"),
            EssSensor(system_coordinator, "version", "pms_build_date"),
            EssSensor(system_coordinator, "version", "pcs_version"),
            EssSensor(system_coordinator, "version", "bms_version"),
            EssSensor(system_coordinator, "version", "bms_unit1_version"),
            EssSensor(system_coordinator, "version", "bms_unit2_version"),
            MeasurementSensor(
                home_coordinator, "statistics", "pcs_pv_total_power", icon=_PV
            ),
            MeasurementSensor(
                home_coordinator, "statistics", "batconv_power", icon=_BATTERYLOAD
            ),
            BinarySensor(home_coordinator, "statistics", "bat_use", icon=_BATTERYHOME),
            MeasurementSensor(
                home_coordinator, "statistics", "bat_status", icon=_BATTERYSTATUS
            ),  # unknown enum
            MeasurementSensor(
                home_coordinator,
                "statistics",
                "bat_user_soc",
                PERCENTAGE,
                icon=_BATTERYHALF,
            ),
            MeasurementSensor(
                home_coordinator, "statistics", "load_power", UnitOfPower.WATT
            ),
            MeasurementSensor(home_coordinator, "statistics", "ac_output_power"),
            MeasurementSensor(home_coordinator, "statistics", "load_today", icon=_LOAD),
            MeasurementSensor(
                home_coordinator,
                "statistics",
                "grid_power",
                UnitOfPower.WATT,
                icon=_GRID,
            ),
            MeasurementSensor(
                home_coordinator,
                "statistics",
                "current_day_self_consumption",
                PERCENTAGE,
                icon=_PV,
            ),
            BinarySensor(
                home_coordinator, "direction", "is_direct_consuming_", icon=_PV
            ),
            BinarySensor(
                home_coordinator, "direction", "is_battery_charging_", icon=_CHARGING
            ),
            BinarySensor(
                home_coordinator,
                "direction",
                "is_battery_discharging_",
                icon=_DISCHARGING,
            ),
            BinarySensor(
                home_coordinator, "direction", "is_grid_selling_", icon=_TOGRID
            ),
            BinarySensor(
                home_coordinator, "direction", "is_grid_buying_", icon=_FROMGRID
            ),
            BinarySensor(
                home_coordinator,
                "direction",
                "is_charging_from_grid_",
                icon=_CHARGING,
            ),
            BinarySensor(
                home_coordinator,
                "direction",
                "is_discharging_to_grid_",
                icon=_DISCHARGING,
            ),
            EssSensor(home_coordinator, "operation", "status"),
            MeasurementSensor(home_coordinator, "operation", "mode"),
            BinarySensor(home_coordinator, "operation", "pcs_standbymode"),
            MeasurementSensor(home_coordinator, "operation", "drm_mode0"),
            MeasurementSensor(home_coordinator, "operation", "remote_mode"),
            MeasurementSensor(home_coordinator, "operation", "drm_control"),
            BinarySensor(home_coordinator, "wintermode", "winter_status", icon=_WINTER),
            BinarySensor(home_coordinator, "wintermode", "backup_status", icon=_BACKUP),
            EssSensor(home_coordinator, "pcs_fault", "pcs_status"),
            EssSensor(home_coordinator, "pcs_fault", "pcs_op_status"),
            MeasurementSensor(
                home_coordinator, "heatpump", "heatpump_protocol", icon=_HEATPUMP
            ),
            BinarySensor(
                home_coordinator, "heatpump", "heatpump_activate", icon=_HEATPUMP
            ),
            MeasurementSensor(
                home_coordinator, "heatpump", "current_temp", icon=_HEATPUMP
            ),
            BinarySensor(
                home_coordinator, "heatpump", "heatpump_working", icon=_HEATPUMP
            ),
            BinarySensor(home_coordinator, "evcharger", "ev_activate", icon=_EV),
            MeasurementSensor(
                home_coordinator, "evcharger", "ev_power", UnitOfPower.WATT, icon=_EV
            ),
            MeasurementSensor(home_coordinator, None, "gridWaitingTime"),
            EssSensor(home_coordinator, None, "backupmode", icon=_BACKUP),
            IncreasingEnergySensor(
                common_coordinator,
                "BATT",
                "today_batt_discharge_enery",
                icon=_DISCHARGING,
            ),
            IncreasingEnergySensor(
                common_coordinator,
                "BATT",
                "today_batt_charge_energy",
                icon=_CHARGING,
            ),
            IncreasingEnergySensor(
                common_coordinator,
                "BATT",
                "month_batt_discharge_energy",
                icon=_DISCHARGING,
            ),
            IncreasingEnergySensor(
                common_coordinator,
                "BATT",
                "month_batt_charge_energy",
                icon=_CHARGING,
            ),
            IncreasingEnergySensor(
                common_coordinator, "LOAD", "today_load_consumption_sum", icon=_LOAD
            ),
            IncreasingEnergySensor(
                common_coordinator,
                "LOAD",
                "today_pv_direct_consumption_enegy",
                icon=_PV,
            ),
            IncreasingEnergySensor(
                common_coordinator,
                "LOAD",
                "today_grid_power_purchase_energy",
                icon=_FROMGRID,
            ),
            IncreasingEnergySensor(
                common_coordinator, "LOAD", "month_load_consumption_sum", icon=_LOAD
            ),
            IncreasingEnergySensor(
                common_coordinator,
                "LOAD",
                "month_pv_direct_consumption_energy",
                icon=_PV,
            ),
            IncreasingEnergySensor(
                common_coordinator,
                "LOAD",
                "month_grid_power_purchase_energy",
                icon=_FROMGRID,
            ),
            IncreasingEnergySensor(
                common_coordinator, "PCS", "today_pv_generation_sum", icon=_PV
            ),
            IncreasingEnergySensor(
                common_coordinator, "PCS", "today_grid_feed_in_energy", icon=_TOGRID
            ),
            IncreasingEnergySensor(
                common_coordinator, "PCS", "month_pv_generation_sum", icon=_PV
            ),
            IncreasingEnergySensor(
                common_coordinator, "PCS", "month_grid_feed_in_energy", icon=_TOGRID
            ),
            MeasurementSensor(
                common_coordinator,
                "PV",
                "pv1_voltage",
                UnitOfElectricPotential.VOLT,
                icon=_ONE,
            ),
            MeasurementSensor(
                common_coordinator,
                "PV",
                "pv2_voltage",
                UnitOfElectricPotential.VOLT,
                icon=_TWO,
            ),
            MeasurementSensor(
                common_coordinator,
                "PV",
                "pv3_voltage",
                UnitOfElectricPotential.VOLT,
                icon=_THREE,
            ),
            MeasurementSensor(
                common_coordinator, "PV", "pv1_power", UnitOfPower.WATT, icon=_ONE
            ),
            MeasurementSensor(
                common_coordinator, "PV", "pv2_power", UnitOfPower.WATT, icon=_TWO
            ),
            MeasurementSensor(
                common_coordinator, "PV", "pv3_power", UnitOfPower.WATT, icon=_THREE
            ),
            MeasurementSensor(
                common_coordinator,
                "PV",
                "pv1_current",
                UnitOfElectricCurrent.AMPERE,
                icon=_ONE,
            ),
            MeasurementSensor(
                common_coordinator,
                "PV",
                "pv2_current",
                UnitOfElectricCurrent.AMPERE,
                icon=_TWO,
            ),
            MeasurementSensor(
                common_coordinator,
                "PV",
                "pv3_current",
                UnitOfElectricCurrent.AMPERE,
                icon=_THREE,
            ),
            IncreasingSensor(
                common_coordinator, "PCS", "month_co2_reduction_accum", icon=_CO2
            ),
            EssSensor(common_coordinator, "PV", "capacity", icon=_PV),  # Wp
            EssSensor(common_coordinator, "BATT", "status", icon=_BATTERYSTATUS),
            BinarySensor(common_coordinator, "BATT", "winter_setting", icon=_WINTER),
            BinarySensor(common_coordinator, "BATT", "winter_status", icon=_WINTER),
            MeasurementSensor(
                common_coordinator, "BATT", "safety_soc", PERCENTAGE, icon=_WINTER
            ),
            BinarySensor(common_coordinator, "BATT", "backup_setting", icon=_BACKUP),
            BinarySensor(common_coordinator, "BATT", "backup_status", icon=_BACKUP),
            MeasurementSensor(
                common_coordinator, "BATT", "backup_soc", PERCENTAGE, icon=_BACKUP
            ),
            MeasurementSensor(
                common_coordinator,
                "GRID",
                "active_power",
                UnitOfPower.WATT,
                icon=_FROMGRID,
            ),
            MeasurementSensor(
                common_coordinator,
                "GRID",
                "a_phase",
                UnitOfElectricPotential.VOLT,
                icon=_GRID,
            ),
            MeasurementSensor(
                common_coordinator, "GRID", "freq", UnitOfFrequency.HERTZ, icon=_GRID
            ),
            EssSensor(common_coordinator, "PCS", "pcs_stauts"),
            MeasurementSensor(
                common_coordinator,
                "PCS",
                "feed_in_limitation",
                PERCENTAGE,
                icon=_TOGRID,
            ),
            EssSensor(common_coordinator, "PCS", "operation_mode"),
        ]
    )


class EssSensor(CoordinatorEntity[ESSCoordinator], SensorEntity):
    """Basic sensor with common functionality."""

    _group: str | None
    _key: str

    def __init__(
        self,
        coordinator,
        group: str | None,
        key: str,
        modify=None,
        icon: str | None = None,
    ) -> None:
        """Initialize the sensor with the common coordinator."""
        super().__init__(coordinator)
        self._group = group
        self._key = key
        self._modify = modify
        if group is None:
            entity = key
        else:
            entity = group + "_" + key
        # Fix typos
        entity = (
            entity.replace("_enery", "_energy")
            .replace("_enegy", "_energy")
            .replace("_stauts", "_status")
        )
        self._attr_translation_key = entity
        self._attr_unique_id = entity
        self._attr_icon = icon

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._group is None:
            _LOGGER.debug("%s : %s", self._key, self.coordinator.data.get(self._key))
            new_value = self.coordinator.data.get(self._key)
        else:
            _LOGGER.debug(
                "%s-%s : %s",
                self._key,
                self._group,
                self.coordinator.data[self._group].get(self._key),
            )
            new_value = self.coordinator.data[self._group].get(self._key)
        if self._modify is not None:
            new_value = self._modify(new_value)
        self._attr_native_value = new_value
        self.async_write_ha_state()


class BinarySensor(CoordinatorEntity[ESSCoordinator], BinarySensorEntity):
    """Binary sensor."""

    _group: str | None
    _key: str

    def __init__(
        self, coordinator, group: str | None, key: str, icon: str | None = None
    ) -> None:
        """Initialize the sensor with the coordinator."""
        super().__init__(coordinator)
        self._group = group
        self._key = key
        if group is None:
            entity = key
        else:
            entity = group + "_" + key
        self._attr_translation_key = entity
        self._attr_unique_id = entity
        self._attr_icon = icon

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._group is None:
            val = self.coordinator.data[self._key]
        else:
            val = self.coordinator.data[self._group][self._key]
        self.is_on = (val == "on") | (val == "true") | (val == "1")
        self.async_write_ha_state()


class MeasurementSensor(EssSensor):
    """Measurement sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator,
        group: str | None,
        key: str,
        unit: str | None = None,
        modify=None,
        icon: str | None = None,
    ) -> None:
        """Initialize the sensor with the common coordinator."""
        super().__init__(coordinator, group, key, modify, icon=icon)
        self._attr_native_unit_of_measurement = unit


class IncreasingSensor(EssSensor):
    """Increasing total sensor."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(
        self,
        coordinator,
        group: str | None,
        key: str,
        unit=UnitOfEnergy.WATT_HOUR,
        icon: str | None = None,
    ) -> None:
        """Initialize the sensor with the coordinator."""
        super().__init__(coordinator, group, key, icon=icon)
        self._attr_native_unit_of_measurement = unit


class IncreasingEnergySensor(IncreasingSensor):
    """Increasing energy Wh sensor."""

    def __init__(
        self, coordinator, group: str | None, key: str, icon: str | None = None
    ) -> None:
        """Initialize the energy sensor with the coordinator."""
        super().__init__(coordinator, group, key, UnitOfEnergy.WATT_HOUR, icon=icon)
        self._attr_suggested_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR


def _parse_date(raw_input: str) -> date:
    return datetime.strptime(raw_input, "%Y-%m-%d").date()
