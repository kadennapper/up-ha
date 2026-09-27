"""UI configuration and options flow for Up Banking."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv

from .api import UpApi
from .const import CONF_ACCOUNTS, CONF_TOKEN, DOMAIN
from .exceptions import UpApiError
from .models import account_label


class UpBankingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a single Up personal access token."""
    VERSION = 1

    def __init__(self) -> None:
        self._token: str | None = None
        self._accounts: list[dict] = []

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            self._token = user_input[CONF_TOKEN].strip()
            try:
                self._accounts = await UpApi(async_get_clientsession(self.hass), self._token).accounts()
            except UpApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id("up_banking")
                self._abort_if_unique_id_configured()
                return await self.async_step_accounts()
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}), errors=errors)

    async def async_step_accounts(self, user_input=None):
        choices = {item["id"]: account_label(item) for item in self._accounts}
        if user_input is not None:
            return self.async_create_entry(title="Up Banking", data={CONF_TOKEN: self._token, CONF_ACCOUNTS: user_input[CONF_ACCOUNTS]})
        return self.async_show_form(step_id="accounts", data_schema=vol.Schema({vol.Required(CONF_ACCOUNTS, default=list(choices)): cv.multi_select(choices)}))

    @staticmethod
    def async_get_options_flow(config_entry):
        return UpBankingOptionsFlow()


class UpBankingOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        try:
            accounts = await UpApi(async_get_clientsession(self.hass), self.config_entry.data[CONF_TOKEN]).accounts()
        except UpApiError:
            return self.async_abort(reason="cannot_connect")
        choices = {item["id"]: account_label(item) for item in accounts}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        selected = self.config_entry.options.get(CONF_ACCOUNTS, self.config_entry.data.get(CONF_ACCOUNTS, []))
        return self.async_show_form(step_id="init", data_schema=vol.Schema({vol.Required(CONF_ACCOUNTS, default=selected): cv.multi_select(choices)}))
