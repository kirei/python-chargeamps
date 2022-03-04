"""Charge-Amps External API Client"""

import asyncio  # noqa
import time
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

import aiohttp
import jwt

from .base import (
    ChargeAmpsClient,
    ChargePoint,
    ChargePointConnectorSettings,
    ChargePointSettings,
    ChargePointStatus,
    ChargingSession,
)

API_BASE_URL = "https://eapi.charge.space"
API_VERSION = "v4"


class ChargeAmpsExternalClient(ChargeAmpsClient):
    def __init__(
        self,
        email: str,
        password: str,
        api_key: str,
        api_base_url: Optional[str] = None,
    ):
        self._email = email
        self._password = password
        self._api_key = api_key
        self._session = aiohttp.ClientSession(raise_for_status=True)
        self._headers = {}
        self._base_url = api_base_url or API_BASE_URL
        self._ssl = False
        self._token = None
        self._token_expire = 0

    async def shutdown(self):
        await self._session.close()

    async def _ensure_token(self):
        if self._token_expire < time.time():
            response = await self._session.post(
                urljoin(self._base_url, f"/api/{API_VERSION}/auth/login"),
                ssl=self._ssl,
                headers={"apiKey": self._api_key},
                json={"email": self._email, "password": self._password},
            )
            self._token = (await response.json())["token"]
            token_payload = jwt.decode(self._token, options={"verify_signature": False})
            self._token_expire = token_payload.get("exp", 0)
            self._headers["Authorization"] = f"Bearer {self._token}"

    async def _post(self, path, **kwargs):
        await self._ensure_token()
        headers = kwargs.pop("headers", self._headers)
        return await self._session.post(
            urljoin(self._base_url, path), ssl=self._ssl, headers=headers, **kwargs
        )

    async def _get(self, path, **kwargs):
        await self._ensure_token()
        headers = kwargs.pop("headers", self._headers)
        return await self._session.get(
            urljoin(self._base_url, path), ssl=self._ssl, headers=headers, **kwargs
        )

    async def _put(self, path, **kwargs):
        await self._ensure_token()
        headers = kwargs.pop("headers", self._headers)
        return await self._session.put(
            urljoin(self._base_url, path), ssl=self._ssl, headers=headers, **kwargs
        )

    async def get_chargepoints(self) -> List[ChargePoint]:
        """Get all owned chargepoints"""
        request_uri = f"/api/{API_VERSION}/chargepoints/owned"
        response = await self._get(request_uri)
        res = []
        for chargepoint in await response.json():
            res.append(ChargePoint.from_dict(chargepoint))
        return res

    async def get_all_chargingsessions(
        self,
        charge_point_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[ChargingSession]:
        """Get all charging sessions"""
        query_params = {}
        if start_time:
            query_params["startTime"] = start_time.isoformat()
        if end_time:
            query_params["endTime"] = end_time.isoformat()
        request_uri = (
            f"/api/{API_VERSION}/chargepoints/{charge_point_id}/chargingsessions"
        )
        response = await self._get(request_uri, params=query_params)
        res = []
        for session in await response.json():
            res.append(ChargingSession.from_dict(session))
        return res

    async def get_chargingsession(
        self, charge_point_id: str, session: int
    ) -> ChargingSession:
        """Get charging session"""
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/chargingsessions/{session}"
        response = await self._get(request_uri)
        return ChargingSession.from_dict(await response.json())

    async def get_chargepoint_status(self, charge_point_id: str) -> ChargePointStatus:
        """Get charge point status"""
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/status"
        response = await self._get(request_uri)
        return ChargePointStatus.from_dict(await response.json())

    async def get_chargepoint_settings(
        self, charge_point_id: str
    ) -> ChargePointSettings:
        """Get chargepoint settings"""
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/settings"
        response = await self._get(request_uri)
        return ChargePointSettings.from_dict(await response.json())

    async def set_chargepoint_settings(self, settings: ChargePointSettings) -> None:
        """Set chargepoint settings"""
        payload = settings.to_dict()
        charge_point_id = settings.id
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/settings"
        await self._put(request_uri, json=payload)

    async def get_chargepoint_connector_settings(
        self, charge_point_id: str, connector_id: int
    ) -> ChargePointConnectorSettings:
        """Get all owned chargepoints"""
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/connectors/{connector_id}/settings"
        response = await self._get(request_uri)
        return ChargePointConnectorSettings.from_dict(await response.json())

    async def set_chargepoint_connector_settings(
        self, settings: ChargePointConnectorSettings
    ) -> None:
        """Get all owned chargepoints"""
        payload = settings.to_dict()
        charge_point_id = settings.charge_point_id
        connector_id = settings.connector_id
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/connectors/{connector_id}/settings"
        await self._put(request_uri, json=payload)
