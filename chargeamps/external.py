"""Charge-Amps External API Client"""

import asyncio  # noqa
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin
import logging

import jwt
from aiohttp import ClientResponse, ClientSession
from aiohttp.web import HTTPException

from .base import ChargeAmpsClient
from .models import (
    ChargePoint,
    ChargePointConnectorSettings,
    ChargePointSettings,
    ChargePointStatus,
    ChargingSession,
    StartAuth,
)

API_BASE_URL = "https://eapi.charge.space"
API_VERSION = "v5"


class ChargeAmpsExternalClient(ChargeAmpsClient):
    def __init__(
        self,
        email: str,
        password: str,
        api_key: str,
        api_base_url: Optional[str] = None,
    ):
        self._logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
        self._email = email
        self._password = password
        self._api_key = api_key
        self._session = ClientSession(raise_for_status=True)
        self._headers = {}
        self._base_url = api_base_url or API_BASE_URL
        self._ssl = False
        self._token = None
        self._token_expire = 0
        self._refresh_token = None

    async def shutdown(self) -> None:
        await self._session.close()

    async def _ensure_token(self) -> None:
        if self._token_expire > time.time():
            return

        if self._token is None:
            self._logger.info("Token not found")
        elif self._token_expire > 0:
            self._logger.info("Token expired")

        response = None

        if self._refresh_token:
            try:
                self._logger.info("Found refresh token, try refresh")
                response = await self._session.post(
                    urljoin(self._base_url, f"/api/{API_VERSION}/auth/refreshToken"),
                    ssl=self._ssl,
                    headers={"apiKey": self._api_key},
                    json={"token": self._token, "refreshToken": self._refresh_token},
                )
                self._logger.debug("Refresh successful")
            except HTTPException:
                self._logger.warning("Token refresh failed")
                self._token = None
                self._refresh_token = None
        else:
            self._token = None

        if self._token is None:
            try:
                self._logger.debug("Try login")
                response = await self._session.post(
                    urljoin(self._base_url, f"/api/{API_VERSION}/auth/login"),
                    ssl=self._ssl,
                    headers={"apiKey": self._api_key},
                    json={"email": self._email, "password": self._password},
                )
                self._logger.debug("Login successful")
            except HTTPException as exc:
                self._logger.error("Login failed")
                self._token = None
                self._refresh_token = None
                self._token_expire = 0
                raise exc

        if response is None:
            self._logger.error("No response")
            return

        response_payload = await response.json()

        self._token = response_payload["token"]
        self._refresh_token = response_payload["refreshToken"]

        token_payload = jwt.decode(self._token, options={"verify_signature": False})
        self._token_expire = token_payload.get("exp", 0)

        self._headers["Authorization"] = f"Bearer {self._token}"

    async def _post(self, path, **kwargs) -> ClientResponse:
        await self._ensure_token()
        headers = kwargs.pop("headers", self._headers)
        return await self._session.post(
            urljoin(self._base_url, path), ssl=self._ssl, headers=headers, **kwargs
        )

    async def _get(self, path, **kwargs) -> ClientResponse:
        await self._ensure_token()
        headers = kwargs.pop("headers", self._headers)
        return await self._session.get(
            urljoin(self._base_url, path), ssl=self._ssl, headers=headers, **kwargs
        )

    async def _put(self, path, **kwargs) -> ClientResponse:
        await self._ensure_token()
        headers = kwargs.pop("headers", self._headers)
        return await self._session.put(
            urljoin(self._base_url, path), ssl=self._ssl, headers=headers, **kwargs
        )

    async def get_chargepoints(self) -> list[ChargePoint]:
        """Get all owned chargepoints"""
        request_uri = f"/api/{API_VERSION}/chargepoints/owned"
        response = await self._get(request_uri)
        res = []
        for chargepoint in await response.json():
            res.append(ChargePoint.model_validate(chargepoint))
        return res

    async def get_all_chargingsessions(
        self,
        charge_point_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[ChargingSession]:
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
            res.append(ChargingSession.model_validate(session))
        return res

    async def get_chargingsession(
        self, charge_point_id: str, session: int
    ) -> ChargingSession:
        """Get charging session"""
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/chargingsessions/{session}"
        response = await self._get(request_uri)
        payload = await response.json()
        return ChargingSession.model_validate(payload)

    async def get_chargepoint_status(self, charge_point_id: str) -> ChargePointStatus:
        """Get charge point status"""
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/status"
        response = await self._get(request_uri)
        payload = await response.json()
        return ChargePointStatus.model_validate(payload)

    async def get_chargepoint_settings(
        self, charge_point_id: str
    ) -> ChargePointSettings:
        """Get chargepoint settings"""
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/settings"
        response = await self._get(request_uri)
        payload = await response.json()
        return ChargePointSettings.model_validate(payload)

    async def set_chargepoint_settings(self, settings: ChargePointSettings) -> None:
        """Set chargepoint settings"""
        payload = settings.model_dump(by_alias=True)
        charge_point_id = settings.id
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/settings"
        await self._put(request_uri, json=payload)

    async def get_chargepoint_connector_settings(
        self, charge_point_id: str, connector_id: int
    ) -> ChargePointConnectorSettings:
        """Get all owned chargepoints"""
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/connectors/{connector_id}/settings"
        response = await self._get(request_uri)
        payload = await response.json()
        return ChargePointConnectorSettings.model_validate(payload)

    async def set_chargepoint_connector_settings(
        self, settings: ChargePointConnectorSettings
    ) -> None:
        """Get all owned chargepoints"""
        payload = settings.model_dump(by_alias=True)
        charge_point_id = settings.charge_point_id
        connector_id = settings.connector_id
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/connectors/{connector_id}/settings"
        await self._put(request_uri, json=payload)

    async def remote_start(
        self, charge_point_id: str, connector_id: int, start_auth: StartAuth
    ) -> None:
        """Remote start chargepoint"""
        payload = start_auth.model_dump(by_alias=True)
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/connectors/{connector_id}/remotestart"
        await self._put(request_uri, json=payload)

    async def remote_stop(self, charge_point_id: str, connector_id: int) -> None:
        """Remote stop chargepoint"""
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/connectors/{connector_id}/remotestop"
        await self._put(request_uri, json="{}")

    async def reboot(self, charge_point_id) -> None:
        """Reboot chargepoint"""
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/reboot"
        await self._put(request_uri, json="{}")
