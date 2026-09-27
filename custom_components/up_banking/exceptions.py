"""Up Banking integration exceptions."""
from homeassistant.exceptions import HomeAssistantError


class UpApiError(HomeAssistantError):
    """Base error returned by the Up API."""


class UpAuthError(UpApiError):
    """The personal access token was rejected."""

