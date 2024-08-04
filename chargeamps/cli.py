"""ChargeAmps Client"""

import argparse
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime

from aiohttp.client_exceptions import ClientResponseError
from ciso8601 import parse_datetime
from isoduration import parse_duration

from . import __version__
from .base import ChargeAmpsClient
from .external import ChargeAmpsExternalClient, StartAuth

logger = logging.getLogger(__name__)

CONFIG_ENV = "CHARGEAMPS_CONFIG"


async def get_chargepoint_id(client: ChargeAmpsClient, args: argparse.Namespace) -> str:
    if args.charge_point_id:
        return args.charge_point_id
    chargepoints = await client.get_chargepoints()
    return chargepoints[0].id


async def command_list_chargepoints(
    client: ChargeAmpsClient, args: argparse.Namespace
) -> None:
    res = []
    for cp in await client.get_chargepoints():
        res.append(cp.model_dump(by_alias=True))
    print(json.dumps(res, indent=4))


async def command_get_chargepoint_status(
    client: ChargeAmpsClient, args: argparse.Namespace
) -> None:
    charge_point_id = await get_chargepoint_id(client, args)
    cp = await client.get_chargepoint_status(charge_point_id)
    if args.connector_id:
        for c in cp.connector_statuses:
            if c.connector_id == args.connector_id:
                print(json.dumps(c.model_dump(by_alias=True), indent=4))
    else:
        print(json.dumps(cp.model_dump(by_alias=True), indent=4))


async def command_get_chargepoint_sessions(
    client: ChargeAmpsClient, args: argparse.Namespace
) -> None:
    charge_point_id = await get_chargepoint_id(client, args)
    if args.session:
        session = await client.get_chargingsession(charge_point_id, args.session)
    else:
        if args.duration is not None:
            start_time = datetime.utcnow() - parse_duration(args.duration)
            end_time = None
        else:
            start_time = parse_datetime(args.start_time) if args.start_time else None
            end_time = parse_datetime(args.end_time) if args.end_time else None
        res = []
        for session in await client.get_all_chargingsessions(
            charge_point_id, start_time, end_time
        ):
            if args.connector_id is None or args.connector_id == session.connector_id:
                res.append(session.model_dump(by_alias=True))
        res = sorted(res, key=lambda i: i["id"])
        print(json.dumps(res, indent=4))


async def command_get_chargepoint_settings(
    client: ChargeAmpsClient, args: argparse.Namespace
) -> None:
    charge_point_id = await get_chargepoint_id(client, args)
    settings = await client.get_chargepoint_settings(charge_point_id)
    print(json.dumps(settings.model_dump(by_alias=True), indent=4))


async def command_set_chargepoint_settings(
    client: ChargeAmpsClient, args: argparse.Namespace
) -> None:
    charge_point_id = await get_chargepoint_id(client, args)
    settings = await client.get_chargepoint_settings(charge_point_id)
    if args.dimmer:
        settings.dimmer = args.dimmer.capitalize()
    if args.downlight is not None:
        settings.down_light = args.downlight
    await client.set_chargepoint_settings(settings)
    settings = await client.get_chargepoint_settings(charge_point_id)
    print(json.dumps(settings.model_dump(by_alias=True), indent=4))


async def command_get_connector_settings(
    client: ChargeAmpsClient, args: argparse.Namespace
) -> None:
    charge_point_id = await get_chargepoint_id(client, args)
    if args.connector_id:
        connector_ids = [args.connector_id]
    else:
        cp = await client.get_chargepoint_status(charge_point_id)
        connector_ids = [c.connector_id for c in cp.connector_statuses]
    res = []
    for connector_id in connector_ids:
        settings = await client.get_chargepoint_connector_settings(
            charge_point_id, connector_id
        )
        res.append(settings.model_dump(by_alias=True))
    print(json.dumps(res, indent=4))


async def command_set_connector_settings(
    client: ChargeAmpsClient, args: argparse.Namespace
) -> None:
    charge_point_id = await get_chargepoint_id(client, args)
    connector_id = args.connector_id
    settings = await client.get_chargepoint_connector_settings(
        charge_point_id, connector_id
    )
    if args.max_current is not None:
        settings.max_current = args.max_current
    if args.enabled is not None:
        settings.mode = "On" if args.enabled else "Off"
    if args.rfid_lock is not None:
        settings.rfid_lock = args.rfid_lock
    if args.cable_lock is not None:
        settings.cable_lock = args.cable_lock
    await client.set_chargepoint_connector_settings(settings)
    settings = await client.get_chargepoint_connector_settings(
        charge_point_id, connector_id
    )
    print(json.dumps(settings.model_dump(by_alias=True), indent=4))


async def command_remote_start(
    client: ChargeAmpsClient, args: argparse.Namespace
) -> None:
    charge_point_id = await get_chargepoint_id(client, args)
    connector_id = args.connector_id
    start_auth = StartAuth(
        rfid_length=len(args.rfid) // 2,
        rfid_format="hex",
        rfid=args.rfid,
        external_transaction_id=str(uuid.uuid4()),
    )
    await client.remote_start(charge_point_id, connector_id, start_auth)


async def command_remote_stop(
    client: ChargeAmpsClient, args: argparse.Namespace
) -> None:
    charge_point_id = await get_chargepoint_id(client, args)
    connector_id = args.connector_id
    await client.remote_stop(charge_point_id, connector_id)


async def command_reboot(client: ChargeAmpsClient, args: argparse.Namespace) -> None:
    charge_point_id = await get_chargepoint_id(client, args)
    await client.reboot(charge_point_id)


def add_arg_chargepoint(parser, required=False):
    parser.add_argument(
        "--chargepoint",
        dest="charge_point_id",
        type=str,
        metavar="ID",
        required=required,
        help="ChargePoint ID",
    )


def add_arg_connector(parser, required=False) -> None:
    parser.add_argument(
        "--connector",
        dest="connector_id",
        type=int,
        metavar="ID",
        required=required,
        help="Connector ID",
    )


async def main_loop() -> None:
    """Main function"""

    parser = argparse.ArgumentParser(description=f"Chargeamps Client v{__version__}")
    parser.add_argument(
        "--config",
        metavar="config",
        default=os.environ.get(CONFIG_ENV),
        help=f"Config file (or set via env {CONFIG_ENV})",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debugging")

    subparsers = parser.add_subparsers(dest="command")

    parser_list = subparsers.add_parser("chargepoints", help="List all chargepoints")
    parser_list.set_defaults(func=command_list_chargepoints)

    parser_status = subparsers.add_parser("status", help="Get chargepoint status")
    parser_status.set_defaults(func=command_get_chargepoint_status)
    add_arg_chargepoint(parser_status)
    add_arg_connector(parser_status)

    parser_sessions = subparsers.add_parser("sessions", help="Get chargepoint sessions")
    parser_sessions.set_defaults(func=command_get_chargepoint_sessions)
    add_arg_chargepoint(parser_sessions)
    add_arg_connector(parser_sessions)
    parser_sessions.add_argument(
        "--session",
        dest="session",
        type=int,
        metavar="ID",
        required=False,
        help="Charging session",
    )
    parser_sessions.add_argument(
        "--start",
        dest="start_time",
        type=str,
        metavar="timestamp",
        help="Include sessions from timestamp",
    )
    parser_sessions.add_argument(
        "--end",
        dest="end_time",
        type=str,
        metavar="timestamp",
        help="Include sessions until timestamp",
    )
    parser_sessions.add_argument(
        "--duration",
        dest="duration",
        type=str,
        metavar="duration",
        help="Include sessions made during a ISO8601 duration",
    )

    parser_get_chargepoint = subparsers.add_parser(
        "get-chargepoint", help="Get chargepoint settings"
    )
    parser_get_chargepoint.set_defaults(func=command_get_chargepoint_settings)
    add_arg_chargepoint(parser_get_chargepoint)

    parser_set_chargepoint = subparsers.add_parser(
        "set-chargepoint", help="Set chargepoint settings"
    )
    parser_set_chargepoint.set_defaults(func=command_set_chargepoint_settings)
    add_arg_chargepoint(parser_set_chargepoint)
    parser_set_chargepoint.add_argument(
        "--dimmer",
        dest="dimmer",
        type=str,
        metavar="",
        choices=["off", "low", "medium", "high"],
        required=False,
        help="Dimmer",
    )
    parser_set_chargepoint.add_argument(
        "--downlight", dest="downlight", action="store_true", help="Enable downlight"
    )
    parser_set_chargepoint.add_argument(
        "--no-downlight",
        dest="downlight",
        action="store_false",
        help="Disable downlight",
    )

    parser_get_connector = subparsers.add_parser(
        "get-connector", aliases=["get"], help="Get connector settings"
    )
    parser_get_connector.set_defaults(func=command_get_connector_settings)
    add_arg_chargepoint(parser_get_connector)
    add_arg_connector(parser_get_connector)

    parser_set_connector = subparsers.add_parser(
        "set-connector", aliases=["set"], help="Change connector settings"
    )
    parser_set_connector.set_defaults(func=command_set_connector_settings)
    add_arg_chargepoint(parser_set_connector)
    add_arg_connector(parser_set_connector, required=True)
    parser_set_connector.add_argument(
        "--enable", dest="enabled", action="store_true", help="Enable connector"
    )
    parser_set_connector.add_argument(
        "--disable", dest="enabled", action="store_false", help="Disable connector"
    )
    parser_set_connector.add_argument(
        "--rfid-lock", dest="rfid_lock", action="store_true", help="Enable RFID lock"
    )
    parser_set_connector.add_argument(
        "--rfid-unlock",
        dest="rfid_lock",
        action="store_false",
        help="Disable RFID lock",
    )
    parser_set_connector.add_argument(
        "--cable-lock", dest="cable_lock", action="store_true", help="Enable cable lock"
    )
    parser_set_connector.add_argument(
        "--cable-unlock",
        dest="cable_lock",
        action="store_false",
        help="Disable cable lock",
    )
    parser_set_connector.add_argument(
        "--current",
        dest="max_current",
        type=int,
        metavar="amps",
        required=False,
        help="Max current",
    )

    parser_remote_start = subparsers.add_parser(
        "start-connector", help="Remote start connector"
    )
    parser_remote_start.set_defaults(func=command_remote_start)
    add_arg_chargepoint(parser_remote_start)
    add_arg_connector(parser_remote_start)
    parser_remote_start.add_argument(
        "--rfid",
        dest="rfid",
        type=str,
        required=True,
        help="RFID identifier",
    )

    parser_remote_stop = subparsers.add_parser(
        "stop-connector", help="Remote stop connector"
    )
    parser_remote_stop.set_defaults(func=command_remote_stop)
    add_arg_chargepoint(parser_remote_stop)
    add_arg_connector(parser_remote_stop)

    parser_reboot = subparsers.add_parser("reboot", help="Reboot chargepoint")
    parser_reboot.set_defaults(func=command_reboot)
    add_arg_chargepoint(parser_reboot)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.config is None:
        parser.print_help()
        sys.exit(-1)

    with open(args.config) as config_file:
        config = json.load(config_file)

    client = ChargeAmpsExternalClient(
        email=config["username"],
        password=config["password"],
        api_key=config["api_key"],
        api_base_url=config.get("api_base_url"),
    )

    try:
        await args.func(client, args)
    except ClientResponseError as exc:
        sys.stderr.write(str(exc))
    except (ValueError, AttributeError) as exc:
        if args.debug:
            raise exc
        parser.print_help()
        await client.shutdown()
        sys.exit(0)

    await client.shutdown()


def main() -> None:
    asyncio.run(main_loop())


if __name__ == "__main__":
    main()
