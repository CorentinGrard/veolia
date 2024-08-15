from datetime import datetime, timedelta
import logging

from veoliAPI import VeoliAPI

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .sensor import VeoliaWaterSensor

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Veolia integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Veolia from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Retrieve username and password from config entry
    username = entry.data["username"]
    password = entry.data["password"]

    # Create an instance of VeoliAPI
    api = VeoliAPI(username=username, password=password)

    # Perform login asynchronously
    try:
        await api.login()
        _LOGGER.info("Successfully logged into Veolia")
    except Exception as e:
        _LOGGER.error(f"Error logging into Veolia: {e}")
        return False

    # Create an update coordinator to fetch data periodically
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Veolia data",
        update_method=lambda: fetch_veolia_data(api),
        update_interval=timedelta(days=1),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Register the sensor platform
    hass.config_entries.async_entry_ids (entry, ["sensor"])

    # Store the coordinator so we can access it later
    hass.data[DOMAIN][entry.entry_id] = coordinator

    return True


async def fetch_veolia_data(api):
    """Fetch the latest data from Veolia API."""
    try:
        now = datetime.now()
        data = await api.get_data(now.year, now.month)
        return data
    except Exception as e:
        _LOGGER.error(f"Error fetching data from Veolia: {e}")
        return None


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
