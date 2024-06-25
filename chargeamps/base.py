"""Base class for ChargeAmps API"""

from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Optional

from .models import (
    ChargePoint,
    ChargePointConnectorSettings,
    ChargePointSettings,
    ChargePointStatus,
    ChargingSession,
    StartAuth,
)


class ChargeAmpsClient(metaclass=ABCMeta):
    @abstractmethod
    async def shutdown(self):
        pass

    @abstractmethod
    async def get_chargepoints(self) -> list[ChargePoint]:
        """Get all owned chargepoints"""
        pass

    @abstractmethod
    async def get_all_chargingsessions(
        self,
        charge_point_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[ChargingSession]:
        """Get all charging sessions"""
        pass

    @abstractmethod
    async def get_chargingsession(
        self, charge_point_id: str, session: int
    ) -> ChargingSession:
        """Get charging session"""
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

    @abstractmethod
    async def remote_start(
        self, charge_point_id: str, connector_id: int, start_auth: StartAuth
    ) -> None:
        """Remote start chargepoint"""
        pass

    @abstractmethod
    async def remote_stop(self, charge_point_id: str, connector_id: int) -> None:
        """Remote stop chargepoint"""
        pass
