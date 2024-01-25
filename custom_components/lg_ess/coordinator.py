"""Coordinator to fetch the data once for all sensors."""

from datetime import timedelta
import logging

from pyess.aio_ess import ESS

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class CommonCoordinator(DataUpdateCoordinator):
    """LG ESS coordinator.

    Data:
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
            _LOGGER,
            # Name of the data. For logging purposes.
            name="LG ESS common",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=5),
        )
        self.ess = ess

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        #        try:
        # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        # handled by the data update coordinator.
        return await self.ess.get_common()
