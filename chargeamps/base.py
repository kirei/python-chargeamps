"""Base class for ChargeAmps API"""

from abc import ABCMeta, abstractmethod

from .models import (
    ChargePoint,
    ChargePointConnector,
    ChargePointConnectorSettings,
    ChargePointConnectorStatus,
    ChargePointSettings,
    ChargePointStatus,
    StartAuth,
)

__all__ = [
    "ChargePoint",
    "ChargePointConnector",
    "ChargePointConnectorStatus",
    "ChargePointConnectorSettings",
    "ChargePointSettings",
    "ChargePointStatus",
    "StartAuth",
]


class ChargeAmpsClient(metaclass=ABCMeta):
    @abstractmethod
    async def shutdown(self) -> None:
        pass

    @abstractmethod
    async def get_chargepoints(self) -> list[ChargePoint]:
        """Get all owned chargepoints"""
        pass

    @abstractmethod
    async def get_chargepoint_status(self, charge_point_id: str) -> ChargePointStatus:
        """Get charge point status"""
        pass

    @abstractmethod
    async def get_chargepoint_settings(
        self, charge_point_id: str
    ) -> ChargePointSettings:
        """Get chargepoint settings"""
        pass

    @abstractmethod
    async def set_chargepoint_settings(self, settings: ChargePointSettings) -> None:
        """Set chargepoint settings"""
        pass

    @abstractmethod
    async def get_chargepoint_connector_settings(
        self, charge_point_id: str, connector_id: int
    ) -> ChargePointConnectorSettings:
        """Get all owned chargepoints"""
        pass

    @abstractmethod
    async def set_chargepoint_connector_settings(
        self, settings: ChargePointConnectorSettings
    ) -> None:
        """Get all owned chargepoints"""
        pass
