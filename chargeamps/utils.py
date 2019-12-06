"""ChargeAmps API utils"""

from dataclasses import field
from datetime import datetime
from typing import Optional

from dataclasses_json import config
from marshmallow import fields


def datetime_encoder(x: Optional[datetime]) -> Optional[str]:
    return datetime.isoformat(x) if x is not None else None

def datetime_decoder(x: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(x) if x is not None else None

datetime_field = field(default=None,
                       metadata=config(encoder=datetime_encoder,
                                       decoder=datetime_decoder,
                                       mm_field=fields.DateTime(format='iso')))
