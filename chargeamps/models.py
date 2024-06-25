"""Data classes for ChargeAmps API"""

from dataclasses import dataclass
from datetime import datetime

from dataclasses_json import LetterCase, dataclass_json

from .utils import datetime_field


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class ChargePointConnector:
    charge_point_id: str
    connector_id: int
    type: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class ChargePoint:
    id: str
    name: str
    password: str
    type: str
    is_loadbalanced: bool
    firmware_version: str
    hardware_version: str
    connectors: list[ChargePointConnector]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class ChargePointMeasurement:
    phase: str
    current: float
    voltage: float


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class ChargePointConnectorStatus:
    charge_point_id: str
    connector_id: int
    total_consumption_kwh: float
    status: str
    measurements: list[ChargePointMeasurement] | None
    start_time: datetime | None = datetime_field()
    end_time: datetime | None = datetime_field()
    session_id: str | None = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class ChargePointStatus:
    id: str
    status: str
    connector_statuses: list[ChargePointConnectorStatus]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=False)
class ChargePointSettings:
    id: str
    dimmer: str
    down_light: bool


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=False)
class ChargePointConnectorSettings:
    charge_point_id: str
    connector_id: int
    mode: str
    rfid_lock: bool
    cable_lock: bool
    max_current: float | None = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class ChargingSession:
    id: str
    charge_point_id: str
    connector_id: int
    session_type: str
    total_consumption_kwh: float
    start_time: datetime | None = datetime_field()
    end_time: datetime | None = datetime_field()


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class StartAuth:
    rfid_length: int
    rfid_format: str
    rfid: str
    external_transaction_id: str
