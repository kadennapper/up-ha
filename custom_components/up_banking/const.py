"""Constants for Up Banking."""
from datetime import timedelta

DOMAIN = "up_banking"
PLATFORMS = ["sensor"]
CONF_TOKEN = "token"
CONF_ACCOUNTS = "accounts"
EVENT_TRANSACTION = "up_banking_transaction"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.seen_transactions"
API_URL = "https://api.up.com.au/api/v1"
