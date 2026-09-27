"""Tests for event payloads: no Home Assistant runtime is required."""
from custom_components.up_banking.models import account_label, transaction_event


def test_account_label_includes_saver_and_ownership():
    account = {"attributes": {"displayName": "Rainy day", "accountType": "SAVER", "ownershipType": "JOINT"}}
    assert account_label(account) == "Rainy day (Saver, Joint)"


def test_transaction_event_is_small_and_automation_ready():
    transaction = {
        "id": "tx-1",
        "attributes": {"status": "HELD", "amount": {"value": "-12.34", "currencyCode": "AUD"}, "description": "Coffee", "createdAt": "2026-01-01T00:00:00Z", "rawText": "Cafe"},
        "relationships": {"account": {"data": {"id": "account-1"}}},
    }
    assert transaction_event(transaction, "created") == {"transaction_id": "tx-1", "event_type": "created", "status": "held", "account_id": "account-1", "amount": "-12.34", "currency": "AUD", "description": "Coffee", "created_at": "2026-01-01T00:00:00Z", "raw_text": "Cafe"}
