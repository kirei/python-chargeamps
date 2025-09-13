import textwrap
from datetime import datetime

from chargeamps.external import ChargeAmpsExternalClient

from .models import (
    ChargePoint,
    ChargePointStatus,
    Organisation,
    OrganisationChargingSession,
    Partner,
    Rfid,
    RfidTag,
    User,
    feature_required,
)

API_BASE_URL = "https://eapi.charge.space"
API_VERSION = "v5"


@feature_required("organisations")
class OrganisationClient(ChargeAmpsExternalClient):
    def __init__(
        self,
        email: str,
        password: str,
        api_key: str,
        api_base_url: str = None,
    ):
        super().__init__(email, password, api_key, api_base_url)

    async def get_organisations(self) -> list[Organisation]:
        """Get all associated organisation's details"""
        request_uri = f"/api/{API_VERSION}/organisations"
        response = await self._get(request_uri)
        payload = await response.json()

        return [Organisation.model_validate(org) for org in payload]

    async def get_organisation(self, org_id: str) -> Organisation:
        """Get organisation details"""
        request_uri = f"/api/{API_VERSION}/organisations/{org_id}"
        response = await self._get(request_uri)
        payload = await response.json()
        return Organisation.model_validate(payload)

    async def get_organisation_chargepoints(self, org_id: str) -> list[ChargePoint]:
        """Get all charge points for organisation"""
        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/chargepoints"
        response = await self._get(request_uri)
        payload = await response.json()

        return [ChargePoint.model_validate(cp) for cp in payload]

    async def get_organisation_chargepoint_statuses(self, org_id: str) -> list[ChargePointStatus]:
        """Get all charge points' status"""
        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/chargepoints/statuses"
        response = await self._get(request_uri)
        payload = await response.json()

        return [ChargePointStatus.model_validate(cp) for cp in payload]

    def is_valid_hex(self, rfid: str) -> bool:
        return len(rfid) % 2 == 0 and all(char in "0123456789ABCDEF" for char in rfid)

    def verify_rfid_length(self, rfid: str, length: int | None = None) -> int:
        length_in_bytes = len(rfid) // 2

        if length and length != length_in_bytes:
            raise ValueError(
                textwrap.dedent(f"""
                The provided RFID does not match the provided length:
                RFID {rfid}, expected length: {length}, calculated length: {length_in_bytes}
            """)
            )

        if length_in_bytes in {4, 7, 10}:
            return length_in_bytes
        else:
            raise ValueError("RFID length invalid, should be either 4, 7 or 10 bytes")

    def verify_rfid(
        self,
        rfid: str,
        rfid_format: str | None,
        rfid_length: str | None,
        rfid_dec_format_length: str | None,
    ) -> dict[str, str]:
        result = {}
        if self.is_valid_hex(rfid):
            result["rfid"] = rfid
        else:
            raise ValueError(f"The provided RFID value is not a valid hex value: rfid: {rfid}")

        rfid_actual_length = self.verify_rfid_length(rfid, rfid_length)
        if rfid_format != "Hex":
            result["rfidFormat"] = rfid_format
            result["rfidLength"] = rfid_actual_length

        if rfid_format == "Hex":
            if rfid_actual_length != 7:
                raise ValueError(
                    "RFID length must be 7 bytes if the (default) format type 'Hex' is set."
                )
        elif rfid_format == "Dec" or rfid_format == "ReverseDec":
            if rfid_dec_format_length:
                result["rfidDecimalFormatLength"] = rfid_dec_format_length
        else:
            raise ValueError("Invalid RFID format")

        return result

    async def get_organisation_charging_sessions(
        self,
        org_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        rfid: str | None = None,
        rfid_format: str = "Hex",  # Possible values: "Hex", "Dec" and "ReverseDec"
        rfid_length: int = None,
        rfid_dec_format_length: int = None,
    ) -> list[OrganisationChargingSession]:
        """Get organisation's charging sessions"""
        query_params = {}
        if start_time:
            query_params["startTime"] = start_time.isoformat()
        if end_time:
            query_params["endTime"] = end_time.isoformat()

        if rfid:
            query_params.update(
                self.verify_rfid(rfid, rfid_format, rfid_length, rfid_dec_format_length)
            )

        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/chargingsessions"
        response = await self._get(request_uri, params=query_params)
        payload = await response.json()

        return [OrganisationChargingSession.model_validate(cp) for cp in payload]

    async def get_partner(self, org_id: str) -> Partner:
        """Get partner details"""
        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/partner"
        response = await self._get(request_uri)
        payload = await response.json()
        return Partner.model_validate(payload)

    async def get_organisation_rfids(self, org_id: str) -> list[RfidTag]:
        """Get organisation's registered rfid tags"""
        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/rfids"
        response = await self._get(request_uri)
        payload = await response.json()

        return [RfidTag.model_validate(cp) for cp in payload]

    async def add_organisation_rfid(
        self, org_id: str, rfid: Rfid, rfid_dec_format_length: int | None = None
    ) -> RfidTag:
        """Add a new RFID tag to the organisation"""
        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/rfids"
        payload = rfid.model_dump(by_alias=True)
        if rfid_dec_format_length:
            payload["rfidDecimalFormatLength"] = rfid_dec_format_length

        response = await self._put(request_uri, json=payload)
        payload = await response.json()
        return RfidTag.model_validate(payload)

    async def get_organisation_rfid(
        self,
        org_id: str,
        rfid: str,
        rfid_format: str = "Hex",  # Possible values: "Hex", "Dec" and "ReverseDec"
        rfid_length: int | None = None,
        rfid_dec_format_length: int | None = None,
    ) -> RfidTag:
        """Get information about a specific RFID tag"""
        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/rfids/{rfid}"
        query_params = {"organisationId": org_id}
        query_params.update(
            self.verify_rfid(rfid, rfid_format, rfid_length, rfid_dec_format_length)
        )

        response = await self._get(request_uri, params=query_params)
        payload = await response.json()
        return RfidTag.model_validate(payload)

    async def revoke_organisation_rfid(self, org_id: str, rfid: Rfid) -> None:
        """Revoke an RFID tag"""
        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/rfids/revoke"
        rfid_id = rfid.rfid
        payload = {"rfid": rfid_id}
        await self._put(request_uri, json=payload)

    async def get_organisation_users(
        self, org_id: str, rfid: bool = False, rfid_dec_format_length: int | None = None
    ) -> list[User]:
        """Get organisation's registered users"""
        query_params = {}
        if rfid_dec_format_length:
            query_params["rfidDecimalFormatLength"] = rfid_dec_format_length
        if rfid:
            query_params["expand"] = "rfid"

        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/users"
        response = await self._get(request_uri, params=query_params)
        payload = await response.json()

        res = []
        for rfid in payload:
            res.append(User.model_validate(rfid))
        return res

    async def add_organisation_user(
        self,
        org_id: str,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        mobile: str | None = None,
        rfid: list[Rfid] | None = None,
        password: str | None = None,
    ) -> User:
        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/users"
        payload = {}

        if first_name:
            payload["firstName"] = first_name
        if last_name:
            payload["lastName"] = last_name
        if email:
            payload["email"] = email
        if mobile:
            payload["mobile"] = mobile
        if rfid:
            payload["rfidTags"] = [tag.model_dump(by_alias=True) for tag in rfid]
        if password:
            if len(password) >= 8:
                payload["password"] = password
            else:
                raise ValueError(
                    "The provided password is too short, must be at least 8 characters"
                )

        response = await self._post(request_uri, json=payload)
        new_user = await response.json()

        return User.model_validate(new_user)

    async def get_organisation_user(
        self,
        org_id: str,
        user_id: str,
        rfid: bool = False,
        rfid_dec_format_length: int | None = None,
    ) -> User:
        """Get organisation's registered users"""
        query_params = {}
        if rfid_dec_format_length:
            query_params["rfidDecimalFormatLength"] = rfid_dec_format_length
        if rfid:
            query_params["expand"] = "rfid"

        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/users/{user_id}"
        response = await self._get(request_uri)
        payload = await response.json()

        return User.model_validate(payload)
