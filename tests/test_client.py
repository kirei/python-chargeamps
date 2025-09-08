import pytest

from chargeamps.external import ChargeAmpsExternalClient


@pytest.mark.asyncio
async def test_external_client():
    _ = ChargeAmpsExternalClient(
        email="user@example.com", password="mekmitasdigoat", api_key="xyzzy"
    )
