"""Base class and data classes for ChargeAmps API"""

from abc import ABCMeta
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from dataclasses_json import LetterCase, dataclass_json

from .utils import datetime_field


class ChargeAmpsClient(metaclass=ABCMeta):
    pass


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class ChargePointConnector(object):
    charge_point_id: str
    connector_id: int
    type: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class ChargePoint(object):
    id: str
    name: str
    password: str
    type: str
    is_loadbalanced: bool
    firmware_version: str
    hardware_version: str
    connectors: List[ChargePointConnector]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class ChargePointMeasurement(object):
    phase: str
    current: float
    voltage: float


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class ChargePointConnectorStatus(object):
    charge_point_id: str
    connector_id: int
    total_consumption_kwh: float
    status: str
    measurements: Optional[List[ChargePointMeasurement]]
    start_time: Optional[datetime] = datetime_field()
    end_time: Optional[datetime] = datetime_field()
    session_id: Optional[str] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class ChargePointStatus(object):
    id: str
    status: str
    connector_statuses: List[ChargePointConnectorStatus]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=False)
class ChargePointSettings(object):
    id: str
    dimmer: str
    down_light: bool


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=False)
class ChargePointConnectorSettings(object):
    charge_point_id: str
    connector_id: int
    mode: str
    rfid_lock: bool
    cable_lock: bool
    max_current: Optional[float] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class ChargingSession(object):
    id: str
    charge_point_id: str
    connector_id: int
    session_type: str
    total_consumption_kwh: float
    start_time: Optional[datetime] = datetime_field()
    end_time: Optional[datetime] = datetime_field()
