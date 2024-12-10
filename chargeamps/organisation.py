from datetime import datetime

from chargeamps.external import ChargeAmpsExternalClient

from .models import (
    ChargePoint,
    ChargePointStatus,
    Rfid,
    RfidTag,
    Partner,
    Organisation,
    User,
    OrganisationChargingSession,
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

        res = []
        for charge_point in payload:
            res.append(ChargePoint.model_validate(charge_point))
        return res

    async def get_organisation_chargepoint_statuses(
        self, org_id: str
    ) -> list[ChargePointStatus]:
        """Get all charge points' status"""
        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/chargepoints/statuses"
        response = await self._get(request_uri)
        payload = await response.json()

        res = []
        for charge_point in payload:
            res.append(ChargePointStatus.model_validate(charge_point))
        return res

    def verify_rfid(
        self, rfid: str, rfid_format: str, rfid_length: str, rfid_dec_format_length: str
    ) -> dict[str, str]:
        result = {}
        result["rfid"] = rfid
        if rfid_format == "Hex":
            # TODO: Should actual `rfid` param be verified against the length here?
            if not rfid_length:
                return result
        elif rfid_format == "Dec" or rfid_format == "ReverseDec":
            if rfid_dec_format_length:
                result["rfidDecimalFormatLength"] = rfid_dec_format_length
        else:
            self._logger.error("Invalid RFID format")
            return {}

        if rfid_length in {4, 7, 10}:
            result["rfidLength"] = rfid_length
        else:
            self._logger.error("RFID length invalid, should be either 4, 7 or 10 bytes")
            return {}

        result["rfidFormat"] = rfid_format
        return result

    async def get_organisation_charging_sessions(
        self,
        org_id: str,
        start_time: datetime = None,
        end_time: datetime = None,
        rfid: str = None,
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

        res = []
        for session in await payload.json():
            res.append(OrganisationChargingSession.model_validate(session))
        return res

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

        res = []
        for rfid in payload:
            res.append(RfidTag.model_validate(rfid))
        return res

    async def add_organisation_rfid(
        self, org_id: str, rfid: Rfid, rfid_dec_format_length: int = None
    ) -> RfidTag:
        """Add a new RFID tag to the organisation"""
        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/rfids"
        payload = rfid.model_dump(by_alias=True)
        if rfid_dec_format_length:
            payload["rfidDecimalFormatLength"] = rfid_dec_format_length
        await self._put(request_uri, json=payload)

    async def get_organisation_rfid(
        self, org_id: str, rfid: Rfid, rfid_format: str = "Hex"
    ) -> RfidTag:
        """Get information about a specific RFID tag"""
        rfid_id = rfid.rfid
        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/rfids/{rfid_id}"
        response = await self._get(request_uri)
        payload = await response.json()
        return RfidTag.model_validate(payload)

    async def revoke_organisation_rfid(self, org_id: str, rfid: Rfid) -> None:
        """Revoke an RFID tag"""
        request_uri = f"/api/{API_VERSION}/organisations/{org_id}/rfids/revoke"
        rfid_id = rfid.rfid
        payload = rfid_id.toJson()
        await self._put(request_uri, json=payload)

    async def get_organisation_users(
        self, org_id: str, rfid: bool = False, rfid_dec_format_length: int = None
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
        first_name: str = None,
        last_name: str = None,
        email: str = None,
        mobile: str = None,
        rfid: [Rfid] = None,
        password: str = None,
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
            payload["rfidTags"] = rfid.model_dump(by_alias=True)
        if password:
            if len(password) >= 8:
                payload["password"] = password
            else:
                raise ValueError(
                    "The provided password is too short, must exceed 8 characters"
                )

        print(payload)
        response = await self._post(request_uri, json=payload)
        new_user = await response.json()

        return User.model_validate(new_user)

    async def get_organisation_user(
        self,
        org_id: str,
        user_id: str,
        rfid: bool = False,
        rfid_dec_format_length: int = None,
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
