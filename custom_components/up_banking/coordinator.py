"""Data coordinator and bounded transaction de-duplication."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import UpApi
from .const import DEFAULT_SCAN_INTERVAL, EVENT_TRANSACTION, STORAGE_KEY, STORAGE_VERSION
from .exceptions import UpApiError
from .models import transaction_event


class UpCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetch account balances and emit only newly observed transaction events."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: UpApi) -> None:
        super().__init__(hass, __import__("logging").getLogger(__name__), name="Up Banking", update_interval=DEFAULT_SCAN_INTERVAL)
        self.entry = entry
        self.api = api
        self._store = Store[dict[str, Any]](hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry.entry_id}")
        self._seen: dict[str, dict[str, Any]] = {}
        self._last_success: str | None = None
        self._primed = False

    async def async_load(self) -> None:
        saved = await self._store.async_load() or {}
        self._seen = saved.get("seen", {})
        self._last_success = saved.get("last_success")
        self._primed = bool(self._seen)

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            accounts = await self.api.accounts()
            enabled = set(self.entry.options.get("accounts", self.entry.data.get("accounts", [])))
            selected = {item["id"]: item for item in accounts if item["id"] in enabled}
            # On first ever setup, establish a baseline rather than replaying banking history.
            since = self._last_success or (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
            transactions = await self.api.transactions_since(since)
        except UpApiError as err:
            raise UpdateFailed(str(err)) from err

        for transaction in reversed(transactions):
            tx_id = transaction["id"]
            status = transaction["attributes"]["status"]
            previous = self._seen.get(tx_id)
            account_id = transaction.get("relationships", {}).get("account", {}).get("data", {}).get("id")
            if self._primed and previous and previous["status"] != status and account_id in selected:
                kind = "settled" if previous["status"] == "HELD" and status == "SETTLED" else "created"
                self.hass.bus.async_fire(EVENT_TRANSACTION, transaction_event(transaction, kind))
            elif self._primed and not previous and account_id in selected:
                self.hass.bus.async_fire(EVENT_TRANSACTION, transaction_event(transaction, "created"))
            self._seen[tx_id] = {"status": status, "event": transaction_event(transaction, "created")}

        for tx_id, saved in list(self._seen.items()):
            if saved["status"] != "HELD":
                continue
            try:
                current = await self.api.transaction(tx_id)
            except UpApiError as err:
                raise UpdateFailed(str(err)) from err
            if current is None:
                # A held item that no longer exists was deleted by Up.
                payload = dict(saved["event"])
                payload.update({"event_type": "deleted", "status": "deleted"})
                if self._primed and payload.get("account_id") in selected:
                    self.hass.bus.async_fire(EVENT_TRANSACTION, payload)
                self._seen.pop(tx_id)
            elif current["attributes"]["status"] == "SETTLED":
                account_id = current.get("relationships", {}).get("account", {}).get("data", {}).get("id")
                if self._primed and account_id in selected:
                    self.hass.bus.async_fire(EVENT_TRANSACTION, transaction_event(current, "settled"))
                self._seen[tx_id] = {"status": "SETTLED", "event": transaction_event(current, "created")}

        self._primed = True
        self._last_success = datetime.now(UTC).isoformat()
        # Retain only a bounded de-duplication window; account/transaction history stays in Up.
        self._seen = dict(list(self._seen.items())[-500:])
        self._store.async_delay_save(lambda: {"seen": self._seen, "last_success": self._last_success}, 10)
        return selected
