from __future__ import annotations

from typing import Any

import voluptuous as vol
from transmission_rpc.error import TransmissionAuthError, TransmissionError

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME

from .const import DEFAULT_PORT, DOMAIN
from .coordinator import create_client

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_USERNAME): str,
        vol.Optional(CONF_PASSWORD): str,
    }
)


class TransmissionStatsConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._async_abort_entries_match(
                {CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]}
            )
            try:
                await self.hass.async_add_executor_job(create_client, user_input)
            except TransmissionAuthError:
                errors["base"] = "invalid_auth"
            except TransmissionError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Transmission ({user_input[CONF_HOST]})", data=user_input
                )
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)
