"""Small, dependency-free asynchronous client for the Up API."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import API_URL
from .exceptions import UpApiError, UpAuthError

_LOGGER = logging.getLogger(__name__)


class UpApi:
    """Read-only Up API client. It deliberately never logs request headers."""

    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        self._session = session
        self._headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    async def accounts(self) -> list[dict[str, Any]]:
        return await self._list("/accounts", {"page[size]": "100"})

    async def transactions_since(self, since: str | None) -> list[dict[str, Any]]:
        params = {"page[size]": "100"}
        if since:
            params["filter[since]"] = since
        return await self._list("/transactions", params, max_pages=10)

    async def held_transactions(self) -> list[dict[str, Any]]:
        """Return the small current set of pending transactions for deletion detection."""
        return await self._list("/transactions", {"page[size]": "100", "filter[status]": "HELD"})

    async def transaction(self, transaction_id: str) -> dict[str, Any] | None:
        """Retrieve a known held transaction; ``None`` means Up deleted it."""
        url = f"{API_URL}/transactions/{transaction_id}"
        try:
            async with self._session.get(url, headers=self._headers, timeout=20) as response:
                if response.status == 404:
                    return None
                if response.status in (401, 403):
                    raise UpAuthError("Personal access token was rejected")
                if response.status >= 400:
                    raise UpApiError(f"Up API request failed ({response.status})")
                return (await response.json())["data"]
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpApiError("Unable to reach the Up API") from err

    async def _list(
        self, path: str, params: dict[str, str], max_pages: int = 2
    ) -> list[dict[str, Any]]:
        url: str | None = f"{API_URL}{path}"
        result: list[dict[str, Any]] = []
        for page in range(max_pages):
            if not url:
                break
            payload = await self._get(url, params if page == 0 else None)
            result.extend(payload.get("data", []))
            url = payload.get("links", {}).get("next")
        return result

    async def _get(self, url: str, params: dict[str, str] | None) -> dict[str, Any]:
        try:
            async with self._session.get(url, headers=self._headers, params=params, timeout=20) as response:
                if response.status in (401, 403):
                    raise UpAuthError("Personal access token was rejected")
                if response.status == 429:
                    raise UpApiError("Up API rate limit reached; will retry on the next update")
                if response.status >= 400:
                    raise UpApiError(f"Up API request failed ({response.status})")
                return await response.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpApiError("Unable to reach the Up API") from err
