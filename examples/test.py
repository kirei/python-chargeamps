import asyncio
import json

from chargeamps.external import ChargeAmpsExternalClient


async def test():
    with open('credentials.json') as input_file:
        c = json.load(input_file)
    client = ChargeAmpsExternalClient(email=c['username'], password=c['password'], api_key=c['api_key'])

    chargepoints = await client.get_chargepoints()
    print(chargepoints)


    status = await client.get_chargepoint_status(chargepoints[0].id)
    print(status)

    status = await client.get_chargingsessions(chargepoints[0].id)
    print(status)

    await client.shutdown()


if __name__ == "__main__":
    asyncio.run(test())
