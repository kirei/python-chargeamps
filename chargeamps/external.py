"""Charge-Amps External API Client"""

import asyncio
import logging
import time
from datetime import datetime
from urllib.parse import urljoin

import httpx
import jwt

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
        api_base_url: str | None = None,
        httpx_client: httpx.AsyncClient | None = None,
    ):
        self._logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
        self._email = email
        self._password = password
        self._api_key = api_key
        self._owns_client = httpx_client is None
        self._httpx_client = httpx_client or httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=15.0, write=15.0, pool=5.0)
        )
        self._headers = {}
        self._base_url = api_base_url or API_BASE_URL
        self._token = None
        self._token_expire = 0
        self._refresh_token = None
        self._token_skew = 30
        self._token_lock = asyncio.Lock()

    async def shutdown(self) -> None:
        if self._owns_client:
            await self._httpx_client.aclose()

    async def _ensure_token(self) -> None:
        if self._token_expire - self._token_skew > time.time():
            return

        if self._token is None:
            self._logger.info("Token not found")
        elif self._token_expire > 0:
            self._logger.info("Token expired")

        async with self._token_lock:
            await self._exclusive_ensure_token()

    async def _exclusive_ensure_token(self) -> None:
        response = None

        if self._refresh_token:
            try:
                self._logger.info("Found refresh token, try refresh")
                response = await self._httpx_client.post(
                    urljoin(self._base_url, f"/api/{API_VERSION}/auth/refreshToken"),
                    headers={"apiKey": self._api_key},
                    json={"token": self._token, "refreshToken": self._refresh_token},
                )
                response.raise_for_status()
                self._logger.debug("Refresh successful")
            except (httpx.HTTPStatusError, httpx.RequestError):
                self._logger.warning("Token refresh failed")
                self._token = None
                self._refresh_token = None
        else:
            self._token = None

        if self._token is None:
            try:
                self._logger.debug("Try login")
                response = await self._httpx_client.post(
                    urljoin(self._base_url, f"/api/{API_VERSION}/auth/login"),
                    headers={"apiKey": self._api_key},
                    json={"email": self._email, "password": self._password},
                )
                response.raise_for_status()
                self._logger.debug("Login successful")
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                self._logger.error("Login failed")
                self._token = None
                self._refresh_token = None
                self._token_expire = 0
                raise exc

        if response is None:
            self._logger.error("No response")
            return

        response_payload = response.json()

        self._token = response_payload["token"]
        self._refresh_token = response_payload["refreshToken"]

        token_payload = jwt.decode(self._token, options={"verify_signature": False})
        self._token_expire = token_payload.get("exp", 0)

        self._headers["Authorization"] = f"Bearer {self._token}"

    async def _httpx_retry(self, method, url, headers, **kwargs) -> httpx.Response:
        try:
            response = await method(url, headers=headers, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                self._token = None
                self._token_expire = 0
                await self._ensure_token()
                response = method(url, headers=headers, **kwargs)
                response.raise_for_status()
                return response
            raise

    async def _post(self, path, **kwargs) -> httpx.Response:
        await self._ensure_token()
        headers = {**self._headers, **kwargs.pop("headers", {})}
        url = urljoin(self._base_url, path)
        response = await self._httpx_retry(self._httpx_client.post, url, headers, **kwargs)
        response.raise_for_status()
        return response

    async def _get(self, path, **kwargs) -> httpx.Response:
        await self._ensure_token()
        headers = {**self._headers, **kwargs.pop("headers", {})}
        url = urljoin(self._base_url, path)
        response = await self._httpx_retry(self._httpx_client.get, url, headers, **kwargs)
        response.raise_for_status()
        return response

    async def _put(self, path, **kwargs) -> httpx.Response:
        await self._ensure_token()
        headers = {**self._headers, **kwargs.pop("headers", {})}
        url = urljoin(self._base_url, path)
        response = await self._httpx_retry(self._httpx_client.put, url, headers, **kwargs)
        response.raise_for_status()
        return response

    async def get_chargepoints(self) -> list[ChargePoint]:
        """Get all owned chargepoints"""
        request_uri = f"/api/{API_VERSION}/chargepoints/owned"
        response = await self._get(request_uri)
        res = []
        for chargepoint in response.json():
            res.append(ChargePoint.model_validate(chargepoint))
        return res

    async def get_all_chargingsessions(
        self,
        charge_point_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[ChargingSession]:
        """Get all charging sessions"""
        query_params = {}
        if start_time:
            query_params["startTime"] = start_time.isoformat()
        if end_time:
            query_params["endTime"] = end_time.isoformat()
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/chargingsessions"
        response = await self._get(request_uri, params=query_params)
        res = []
        for session in response.json():
            res.append(ChargingSession.model_validate(session))
        return res

    async def get_chargingsession(self, charge_point_id: str, session: int) -> ChargingSession:
        """Get charging session"""
        request_uri = (
            f"/api/{API_VERSION}/chargepoints/{charge_point_id}/chargingsessions/{session}"
        )
        response = await self._get(request_uri)
        payload = response.json()
        return ChargingSession.model_validate(payload)

    async def get_chargepoint_status(self, charge_point_id: str) -> ChargePointStatus:
        """Get charge point status"""
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/status"
        response = await self._get(request_uri)
        payload = response.json()
        return ChargePointStatus.model_validate(payload)

    async def get_chargepoint_settings(self, charge_point_id: str) -> ChargePointSettings:
        """Get chargepoint settings"""
        request_uri = f"/api/{API_VERSION}/chargepoints/{charge_point_id}/settings"
        response = await self._get(request_uri)
        payload = response.json()
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
        request_uri = (
            f"/api/{API_VERSION}/chargepoints/{charge_point_id}/connectors/{connector_id}/settings"
        )
        response = await self._get(request_uri)
        payload = response.json()
        return ChargePointConnectorSettings.model_validate(payload)

    async def set_chargepoint_connector_settings(
        self, settings: ChargePointConnectorSettings
    ) -> None:
        """Get all owned chargepoints"""
        payload = settings.model_dump(by_alias=True)
        charge_point_id = settings.charge_point_id
        connector_id = settings.connector_id
        request_uri = (
            f"/api/{API_VERSION}/chargepoints/{charge_point_id}/connectors/{connector_id}/settings"
        )
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
