import asyncio
import json

from chargeamps.external import ChargeAmpsExternalClient


async def test():
    with open("credentials.json") as input_file:
        c = json.load(input_file)
    client = ChargeAmpsExternalClient(
        email=c["username"], password=c["password"], api_key=c["api_key"]
    )

    chargepoints = await client.get_chargepoints()
    print(chargepoints)

    status = await client.get_chargepoint_status(chargepoints[0].id)
    print("Status:", status)

    for c in status.connector_statuses:
        settings = await client.get_chargepoint_connector_settings(
            c.charge_point_id, c.connector_id
        )
        print("Before:", settings)
        settings.max_current = 6
        await client.set_chargepoint_connector_settings(settings)
        print("After:", settings)

    await client.shutdown()


if __name__ == "__main__":
    # asyncio.run(test())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
