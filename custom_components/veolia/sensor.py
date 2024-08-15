from datetime import datetime, timedelta
import itertools
import statistics

from homeassistant_historical_sensor import (
    HistoricalSensor,
    HistoricalState,
    PollUpdateMixin,
)
from veoliAPI import VeoliAPI

from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.util import dt as dtutil

from .const import DOMAIN

PLATFORM = "sensor"


class Sensor(PollUpdateMixin, HistoricalSensor, SensorEntity):
    #
    # Base clases:
    # - SensorEntity: This is a sensor, obvious
    # - HistoricalSensor: This sensor implements historical sensor methods
    # - PollUpdateMixin: Historical sensors disable poll, this mixing
    #                    reenables poll only for historical states and not for
    #                    present state
    #

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._attr_has_entity_name = True
        self._attr_name = DOMAIN

        self._attr_unique_id = DOMAIN
        self._attr_entity_id = DOMAIN

        self._attr_entity_registry_enabled_default = True
        self._attr_state = None

        # Define whatever you are
        self._attr_native_unit_of_measurement = UnitOfVolume.LITERS
        self._attr_device_class = SensorDeviceClass.WATER

        # We DON'T opt-in for statistics (don't set state_class). Why?
        #
        # Those statistics are generated from a real sensor, this sensor, but we don't
        # want that hass try to do anything with those statistics because we
        # (HistoricalSensor) handle generation and importing
        #
        # self._attr_state_class = SensorStateClass.MEASUREMENT

        self.api = VeoliAPI()
        self.api.login()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

    async def async_update_historical(self):
        # Fill `HistoricalSensor._attr_historical_states` with HistoricalState's
        # This functions is equivaled to the `Sensor.async_update` from
        # HomeAssistant core
        #
        # Important: You must provide datetime with tzinfo

        hist_states = [
            HistoricalState(
                state=state,
                dt=dtutil.as_local(dt),  # Add tzinfo, required by HistoricalSensor
            )
            for (dt, state) in self.api.fetch(
                start=datetime.now() - timedelta(days=3), step=timedelta(minutes=15)
            )
        ]
        self._attr_historical_states = hist_states

    @property
    def statistic_id(self) -> str:
        return self.entity_id

    def get_statistic_metadata(self) -> StatisticMetaData:
        #
        # Add sum and mean to base statistics metadata
        # Important: HistoricalSensor.get_statistic_metadata returns an
        # internal source by default.
        #
        meta = super().get_statistic_metadata()
        meta["has_sum"] = True
        meta["has_mean"] = True

        return meta

    async def async_calculate_statistic_data(
        self, hist_states: list[HistoricalState], *, latest: dict | None = None
    ) -> list[StatisticData]:
        #
        # Group historical states by hour
        # Calculate sum, mean, etc...
        #

        accumulated = latest["sum"] if latest else 0

        def hour_block_for_hist_state(hist_state: HistoricalState) -> datetime:
            # XX:00:00 states belongs to previous hour block
            if hist_state.dt.minute == 0 and hist_state.dt.second == 0:
                dt = hist_state.dt - timedelta(hours=1)
                return dt.replace(minute=0, second=0, microsecond=0)

            else:
                return hist_state.dt.replace(minute=0, second=0, microsecond=0)

        ret = []
        for dt, collection_it in itertools.groupby(
            hist_states, key=hour_block_for_hist_state
        ):
            collection = list(collection_it)
            mean = statistics.mean([x.state for x in collection])
            partial_sum = sum([x.state for x in collection])
            accumulated = accumulated + partial_sum

            ret.append(
                StatisticData(
                    start=dt,
                    state=partial_sum,
                    mean=mean,
                    sum=accumulated,
                )
            )

        return ret


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,  # noqa DiscoveryInfoType | None
):
    device_info = hass.data[DOMAIN][config_entry.entry_id]
    sensors = [
        Sensor(config_entry=config_entry, device_info=device_info),
    ]
    async_add_devices(sensors)
