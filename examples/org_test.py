import asyncio
import json

from chargeamps.organisation import OrganisationClient


async def test():
    with open("config.json") as input_file:
        c = json.load(input_file)
    client = OrganisationClient(email=c["username"], password=c["password"], api_key=c["api_key"])

    chargepoints = await client.get_organisation_chargepoints()
    print(chargepoints)

    status = await client.get_chargepoint_status(chargepoints[0].id)
    print("Status:", status)

    for c in status.connector_statuses:
        settings = await client.get_chargepoint_connector_settings(
            c.charge_point_id, c.connector_id
        )
        print("Before:", settings)
        settings.max_current = 11
        await client.set_chargepoint_connector_settings(settings)
        print("After:", settings)

    await client.shutdown()


if __name__ == "__main__":
    asyncio.run(test())
