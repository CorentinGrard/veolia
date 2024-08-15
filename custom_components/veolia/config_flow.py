from veoliAPI import VeoliAPI
import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN


class VeoliaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Veolia."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None) -> dict:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                # Create an instance of VeoliAPI
                veolia = VeoliAPI(user_input["username"], user_input["password"])

                # Perform login asynchronously
                await veolia.login()

                # Create the entry if authentication is successful
                return self.async_create_entry(title="Veolia Water", data=user_input)
            except Exception as e:
                # Handle errors and provide feedback
                errors["base"] = "auth"
                self.hass.logger.error(f"Veolia authentication failed: {e}")

        # Display the form if user input is not yet provided or authentication failed
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("username", description="Username"): str,
                    vol.Required("password", description="Password"): str,
                }
            ),
            errors=errors,
        )
