from datetime import timedelta
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import DEVICE_CLASS_WATER, UNIT_LITERS
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Veolia sensor platform."""
    username = config_entry.data["username"]
    password = config_entry.data["password"]

    # Create an instance of the VeoliAPI and authenticate
    from veoliAPI import VeoliAPI
    veoliAPI = VeoliAPI(username, password)
    veoliAPI.login()

    async def async_update_data():
        """Fetch data from Veolia API."""
        _LOGGER.info("Fetching data from Veolia API")
        try:
            # Update to current year and month
            from datetime import datetime
            now = datetime.now()
            data = veoliAPI.get_data(now.year, now.month)
            return data
        except Exception as e:
            _LOGGER.error(f"Error fetching data: {e}")
            return []

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Veolia water consumption",
        update_method=async_update_data,
        update_interval=timedelta(days=1),  # Fetch data daily
    )

    await coordinator.async_config_entry_first_refresh()

    # Create sensor entities based on the fetched data
    entities = []
    for entry in coordinator.data:
        entities.append(VeoliaWaterSensor(coordinator, entry))

    async_add_entities(entities, update_before_add=True)


class VeoliaWaterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Veolia Water Sensor."""

    def __init__(self, coordinator, entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._state = entry['consommation']['litre']
        self._name = f"Veolia Water {entry['date_releve']}"
        self._unique_id = f"veolia_{entry['date_releve']}"
        self._device_class = DEVICE_CLASS_WATER

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._entry['consommation']['litre']

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return UNIT_LITERS

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id
