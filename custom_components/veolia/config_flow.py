import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN

class VeoliaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Veolia."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # Try to authenticate with the user input
            try:
                from veoliAPI import VeoliaAuthenticator
                authenticator = VeoliaAuthenticator(user_input["username"], user_input["password"])
                authenticator.login()
                return self.async_create_entry(title="Veolia Water", data=user_input)
            except Exception:
                errors["base"] = "auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("username"): str,
                vol.Required("password"): str,
            }),
            errors=errors,
        )
