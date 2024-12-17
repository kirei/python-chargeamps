"""Data models for ChargeAmps API"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, PlainSerializer
from pydantic.alias_generators import to_camel
from typing_extensions import Annotated

CustomDateTime = Annotated[
    datetime,
    PlainSerializer(
        lambda _datetime: _datetime.strftime("%Y-%m-%dT%H:%M:%SZ"), return_type=str
    ),
]


def feature_required(feature_flag):
    def decorator(cls):
        if feature_flag == "organisations":
            return cls
        else:
            raise ImportError(f"Feature '{feature_flag}' is not enabled")

    return decorator


class FrozenBaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        frozen=True,
    )


class ChargePointConnector(FrozenBaseSchema):
    charge_point_id: str
    connector_id: int
    type: str


class ChargePoint(FrozenBaseSchema):
    id: str
    name: str
    password: str
    type: str
    is_loadbalanced: bool
    firmware_version: str
    hardware_version: str
    connectors: list[ChargePointConnector]


class ChargePointMeasurement(FrozenBaseSchema):
    phase: str
    current: float
    voltage: float


class ChargePointConnectorStatus(FrozenBaseSchema):
    charge_point_id: str
    connector_id: int
    total_consumption_kwh: float
    status: str
    measurements: Optional[list[ChargePointMeasurement]]
    start_time: Optional[CustomDateTime] = None
    end_time: Optional[CustomDateTime] = None
    session_id: Optional[int] = None


class ChargePointStatus(FrozenBaseSchema):
    id: str
    status: str
    connector_statuses: list[ChargePointConnectorStatus]


class ChargePointSettings(FrozenBaseSchema):
    id: str
    dimmer: str
    down_light: bool


class ChargePointConnectorSettings(FrozenBaseSchema):
    charge_point_id: str
    connector_id: int
    mode: str
    rfid_lock: bool
    cable_lock: bool
    max_current: Optional[float] = None


class ChargingSession(FrozenBaseSchema):
    id: int
    charge_point_id: str
    connector_id: int
    session_type: str
    total_consumption_kwh: float
    start_time: Optional[CustomDateTime] = None
    end_time: Optional[CustomDateTime] = None


class StartAuth(FrozenBaseSchema):
    rfid_length: int
    rfid_format: str
    rfid: str
    external_transaction_id: str


class RfidTag(FrozenBaseSchema):
    active: bool
    rfid: str | None
    rfidDec: str | None
    rfidDecReverse: str | None


class User(FrozenBaseSchema):
    id: str
    first_name: str | None
    last_name: str | None
    email: str | None
    mobile: str | None
    rfid_tags: Optional[list[RfidTag]]
    user_status: str


class Partner(FrozenBaseSchema):
    id: int
    name: str
    description: str
    email: str
    phone: str


# Only way to register new RFID seems to be through an Organization
@feature_required("organisations")
class Rfid(FrozenBaseSchema):
    rfid: str | None
    rfidDec: str | None
    rfidDecReverse: str | None


@feature_required("organisations")
class Organisation(FrozenBaseSchema):
    id: str
    name: str
    description: str


@feature_required("organisations")
class OrganisationChargingSession(FrozenBaseSchema):
    id: int
    charge_point_id: Optional[str]
    connector_id: int
    user_id: str
    rfid: Optional[str]
    rfidDec: Optional[str]
    rfidDecReverse: Optional[str]
    organisation_id: Optional[str]
    session_type: str
    start_time: Optional[CustomDateTime] = None
    end_time: Optional[CustomDateTime] = None
    external_transaction_id: Optional[str]
    total_consumption_kwh: float
    external_id: Optional[str]
