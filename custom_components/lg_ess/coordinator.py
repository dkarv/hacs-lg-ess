"""Coordinator to fetch the data once for all sensors."""

from datetime import timedelta
import logging

from pyess.aio_ess import ESS

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class ESSCoordinator(DataUpdateCoordinator):
    """LG ESS basic coordinator."""

    _ess: ESS

    def __init__(
        self, hass: HomeAssistant, ess: ESS, name: str, interval: timedelta
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=interval,
        )
        self._ess = ess


class CommonCoordinator(ESSCoordinator):
    """LG ESS common coordinator.

    {'PV':
        {'brand': 'LGE-SOLAR', 'capacity': '10935',
            'pv1_voltage': '52.900002', 'pv2_voltage': '36.099998', 'pv3_voltage': '35.500000',
            'pv1_power': '0', 'pv2_power': '1', 'pv3_power': '1',
            'pv1_current': '0.010000', 'pv2_current': '0.030000', 'pv3_current': '0.030000',
            'today_pv_generation_sum': '16294', 'today_month_pv_generation_sum': '17469'},
    'BATT':
        {'status': '2', 'soc': '10.3', 'dc_power': '627',
            'winter_setting': 'off', 'winter_status': 'off', 'safety_soc': '20',
            'backup_setting': 'off', 'backup_status': 'off', 'backup_soc': '30',
            'today_batt_discharge_enery': '6855', 'today_batt_charge_energy': '9050', 'month_batt_charge_energy': '9616', 'month_batt_discharge_energy': '9264'},
    'GRID':
        {'active_power': '9', 'a_phase': '230.199997', 'freq': '50.020000',
            'today_grid_feed_in_energy': '968', 'today_grid_power_purchase_energy': '7442',
            'month_grid_feed_in_energy': '994', 'month_grid_power_purchase_energy': '13497'},
    'LOAD':
        {'load_power': '638',
            'today_load_consumption_sum': '20573', 'today_pv_direct_consumption_enegy': '6276', 'today_batt_discharge_enery': '6855', 'today_grid_power_purchase_energy': '7442',
            'month_load_consumption_sum': '29620', 'month_pv_direct_consumption_energy': '6859', 'month_batt_discharge_energy': '9264', 'month_grid_power_purchase_energy': '13497'},
    'PCS':
        {'today_self_consumption': '94.1', 'month_co2_reduction_accum': '12402',
            'today_pv_generation_sum': '16294', 'today_grid_feed_in_energy': '968',
            'month_pv_generation_sum': '17469', 'month_grid_feed_in_energy': '994',
            'pcs_stauts': '3', 'feed_in_limitation': '100', 'operation_mode': '0'}}
    """

    def __init__(self, hass: HomeAssistant, ess: ESS) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            ess,
            name="LG ESS common",
            interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        return await self._ess.get_common()


class SystemInfoCoordinator(ESSCoordinator):
    """LG ESS system info coordinator.

    {'pms':
        {'model': 'XXXXXXXXXXX', 'serialno': 'XXXXXXXXXXXXXXXX', 'ac_input_power': '13500', 'ac_output_power': '10', 'install_date': 'YYYY-MM-DD'},
    'batt':
        {'capacity': '160', 'type': 'hbp', 'hbc_cycle_count_1': '0', 'hbc_cycle_count_2': '0', 'install_date': 'YYYY-MM-DD'},
    'version':
        {'pms_version': 'AA.BB.CCCC', 'pms_build_date': 'YYYY-MM-DD XXXXX', 'pcs_version': 'LG 05.00.01.00 XXXX A.BBB.C',
        'bms_version': 'BMS 02.03.00.04 / DCDC 16.11.0.0 ', 'bms_unit1_version': 'BMS 02.03.00.04 / DCDC 16.11.0.0 ', 'bms_unit2_version': ' '}}
    """

    def __init__(self, hass: HomeAssistant, ess: ESS) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            ess,
            name="LG ESS system info",
            interval=timedelta(minutes=10),
        )

    async def _async_update_data(self):
        return await self._ess.get_systeminfo()


class HomeCoordinator(ESSCoordinator):
    """LG ESS system info coordinator.

    {'statistics':
        {'pcs_pv_total_power': '0', 'batconv_power': '540', 'bat_use': '1', 'bat_status': '2', 'bat_user_soc': '61.4',
        'load_power': '541', 'ac_output_power': '10', 'load_today': '0.0', 'grid_power': '0',
        'current_day_self_consumption': '81.6', 'current_pv_generation_sum': '26191', 'current_grid_feed_in_energy': '4810'},
    'direction':
        {'is_direct_consuming_': '0', 'is_battery_charging_': '0', 'is_battery_discharging_': '1', 'is_grid_selling_': '0',
        'is_grid_buying_': '0', 'is_charging_from_grid_': '0', 'is_discharging_to_grid_': '0'},
    'operation':
        {'status': 'start', 'mode': '1', 'pcs_standbymode': 'false', 'drm_mode0': '0', 'remote_mode': '0', 'drm_control': '0'},
    'wintermode':
        {'winter_status': 'off', 'backup_status': 'off'},
    'backupmode': '',
    'pcs_fault':
        {'pcs_status': 'pcs_ok', 'pcs_op_status': 'pcs_run'},
    'heatpump':
        {'heatpump_protocol': '0', 'heatpump_activate': 'off', 'current_temp': '0', 'heatpump_working': 'off'},
    'evcharger':
        {'ev_activate': 'off', 'ev_power': '0'},
    'gridWaitingTime': '0'}
    """

    def __init__(self, hass: HomeAssistant, ess: ESS) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            ess,
            name="LG ESS home",
            interval=timedelta(seconds=10),
        )

    async def _async_update_data(self):
        return await self._ess.get_home()
