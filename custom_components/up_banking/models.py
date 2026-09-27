"""Pure data conversion helpers kept independent of Home Assistant."""
from __future__ import annotations

from typing import Any


def account_label(account: dict[str, Any]) -> str:
    """Human friendly account label used only in UI, never as an identifier."""
    attrs = account["attributes"]
    return f"{attrs['displayName']} ({attrs['accountType'].title()}, {attrs['ownershipType'].title()})"


def transaction_event(transaction: dict[str, Any], event_type: str) -> dict[str, Any]:
    """Return the deliberately small, automation-oriented event payload."""
    attrs = transaction["attributes"]
    money = attrs["amount"]
    account = transaction.get("relationships", {}).get("account", {}).get("data", {})
    return {
        "transaction_id": transaction["id"],
        "event_type": event_type,
        "status": attrs["status"].lower(),
        "account_id": account.get("id"),
        "amount": money["value"],
        "currency": money["currencyCode"],
        "description": attrs.get("description", ""),
        "created_at": attrs.get("createdAt"),
        "raw_text": attrs.get("rawText"),
    }
