"""Balance sensors for selected Up accounts."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_AUSTRALIAN_DOLLAR
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import UpCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: UpCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(UpBalanceSensor(coordinator, account_id) for account_id in coordinator.data)


class UpBalanceSensor(CoordinatorEntity[UpCoordinator], SensorEntity):
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = CURRENCY_AUSTRALIAN_DOLLAR
    _attr_has_entity_name = True

    def __init__(self, coordinator: UpCoordinator, account_id: str) -> None:
        super().__init__(coordinator)
        self._account_id = account_id
        self._attr_unique_id = f"{account_id}_balance"

    @property
    def _account(self) -> dict[str, Any]:
        return self.coordinator.data[self._account_id]

    @property
    def name(self) -> str:
        return f"{self._account['attributes']['displayName']} balance"

    @property
    def native_value(self) -> Decimal:
        return Decimal(self._account["attributes"]["balance"]["value"])

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        attrs = self._account["attributes"]
        return {"account_type": attrs["accountType"].lower(), "ownership_type": attrs["ownershipType"].lower()}

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.coordinator.entry.entry_id)}, name="Up Banking", manufacturer="Up Banking")
