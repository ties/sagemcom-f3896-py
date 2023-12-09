import asyncio
import datetime
import json
import re
import time

import aiohttp
import click

from sagemcom_f3896_client.models import EventLogItem
from sagemcom_f3896_client.util import build_client

RE_MAC_ADDRESS: re.Pattern = re.compile(
    r"(?P<prefix>([0-9A-Fa-f]{2}[:-]){3})([0-9A-Fa-f]{2}[:-]){2}([0-9A-Fa-f]{2})",
    re.IGNORECASE,
)


async def print_downstreams():
    """Print the downstream channels of the modem."""
    async with build_client() as client:
        primary = await client.modem_primary_downstream()

        for ch in await client.modem_downstreams():
            lock_status = "locked" if ch.lock_status else "unlocked"
            match ch.channel_type:
                case "sc_qam":
                    click.echo(
                        click.style(
                            f"{ch.channel_type:<6} {ch.channel_id:>3} {ch.frequency:>8} {ch.power:>4} {ch.snr:>9} {ch.modulation:>8} {ch.rx_mer / 1.0:>4} {lock_status:>8} {ch.corrected_errors:>10} {ch.uncorrected_errors:>3}",
                            bold=ch.channel_id == primary.channel_id,
                        )
                    )
                case "ofdm":
                    click.echo(
                        click.style(f"{ch.channel_type:<6}", fg="green")
                        + f" {ch.channel_id:>3} {ch.frequency:>8} {ch.power:>4} {ch.channel_width:>9} {ch.modulation:>8} {ch.rx_mer:>4} {lock_status :>8} {ch.fft_type:>3} {ch.number_of_active_subcarriers:>4} {ch.corrected_errors:>10} {ch.uncorrected_errors:>3}"
                    )


async def print_upstreams():
    async with build_client() as client:
        for ch in await client.modem_upstreams():
            lock_status = "locked" if ch.lock_status else "unlocked"
            match ch.channel_type:
                case "atdma":
                    click.echo(
                        f"{ch.channel_type:<6} {ch.channel_id:>2} {ch.frequency:>8} {round(ch.power, 1):>4} {ch.symbol_rate:>5} {ch.modulation:>6} {lock_status:>8} {ch.t1_timeouts:>2} {ch.t2_timeouts:>2} {ch.t3_timeouts:>2} {ch.t4_timeouts:>2}"
                    )
                case "ofdma":
                    click.echo(
                        click.style(f"{ch.channel_type:<6}", fg="green")
                        + f" {ch.channel_id:>2} {ch.frequency:>8} {round(ch.power, 1):>4} {ch.channel_width:>5} {ch.modulation:>6} {lock_status:>8} {ch.number_of_active_subcarriers:>4} {ch.fft_type:>4} {ch.t3_timeouts:>2} {ch.t4_timeouts:>2}"
                    )


async def print_log(
    dump_json: bool = False,
    dump_bbcode: bool = False,
    limit: int = 10,
    remove_mac: bool = False,
):
    """(pretty) print the modem log."""
    async with build_client() as client:
        entries = await client.modem_event_log()

        def clean_message(entry: EventLogItem) -> str:
            return (
                RE_MAC_ADDRESS.sub(r"\g<prefix>xx:xx:xx", entry.message)
                if remove_mac
                else entry.message
            )

        if limit > 0:
            entries = entries[:limit]

        for entry in entries:
            match entry.priority:
                case "critical":
                    priority = click.style(f"{entry.priority:<9}", fg="red", bold=True)
                case "error":
                    priority = click.style(f"{entry.priority:<9}", fg="red")
                case "notice":
                    priority = click.style(f"{entry.priority:<9}", fg="green")
                case _:
                    priority = entry.priority

            click.echo(f"{entry.time.ctime()} {priority} {clean_message(entry)}")

        if dump_bbcode:
            click.echo("[table border=1 width=800 cellpadding=2 bordercolor=#000000]")
            click.echo(
                "  [tr][td][b]Time[/b][/td][td][b]Priority[/b][/td][td][b]Message[/b][/td][/tr]"
            )
            for entry in entries:
                click.echo(
                    f"  [tr][td]{entry.time.ctime()}[/td][td]{f'[b]{priority}[/b]' if priority == 'critical' else 'critical'}[/td][td]{clean_message(entry)}[/td][/tr]"
                )
            click.echo("[/table]")

        if dump_json:
            click.echo(json.dumps([e.message for e in entries]))


async def print_status():
    async with build_client() as client:
        system_state = await client.system_state()
        system_info = await client.system_info()
        click.echo("| ---------------- | ---------------------------- |")
        click.echo(f"| Model            | {system_info.model_name:>28} |")
        click.echo(f"| MAC address      | {system_state.mac_address:>28} |")
        click.echo(f"| Serial number    | {system_state.serial_number:>28} |")
        click.echo(f"| Hardware version | {system_info.hardware_version:>28} |")
        click.echo(f"| Software version | {system_info.software_version:>28} |")
        uptime = datetime.timedelta(seconds=system_state.up_time)
        click.echo(f"| Uptime           | {str(uptime):>28} |")
        click.echo(f"| Boot file        | {system_state.boot_file_name:>28} |")
        click.echo(f"| DOCSIS version   | {system_state.docsis_version:>28} |")
        click.echo(f"| Status           | {system_state.status:>28} |")
        click.echo(f"| Max CPEs         | {system_state.max_cpes:>28} |")
        click.echo(f"| Access allowed   | {system_state.access_allowed:>28} |")
        click.echo("| ---------------- | ---------------------------- |")


async def print_service_flows():
    async with build_client() as client:
        service_flows = await client.modem_service_flows()
        click.echo(
            "| ------ | ---------- | ---------------- | ------ | ---- | ------- | ------------- |"
        )
        click.echo(
            f"| {'ID':>6} | {'direction':>10} | {'max rate':>16} | {'burst':>6} | {'res':>4} | {'concat':>7} | {'schedule type':>13} |"
        )
        click.echo(
            "| ------ | ---------- | ---------------- | ------ | ---- | ------- | ------------- |"
        )
        # id=216806, direction='downstream', max_traffic_rate=1070000000, max_traffic_burst=96000, min_reserved_rate=0, max_concatenated_burst=0, schedule_type='undefined')
        for sf in service_flows:
            click.echo(
                f"| {sf.id:>6} | {sf.direction:>10} | {sf.max_traffic_rate:>16} | {sf.max_traffic_burst:>6} | {sf.min_reserved_rate:>4} | {sf.max_concatenated_burst:>7} | {sf.schedule_type:>13} |"
            )
        click.echo(
            "| ------ | ---------- | ---------------- | ------ | ---- | ------- | ------------- |"
        )


async def do_reboot():
    t0 = time.time()
    click.echo("Rebooting modem...", color="red")
    async with build_client(timeout=30) as client:
        await client.system_reboot()
    click.echo(f"Modem rebooted in {time.time() - t0:.2f}s", color="green")
    async with build_client(timeout=1) as client:
        had_failure = False

        width = 0
        while True:
            width += 1
            try:
                res = await client.echo({"ping": True})
                click.echo(".", nl=width % 80 == 0)
                if (res is not None and res["ping"]) and had_failure:
                    break
            except (
                asyncio.TimeoutError,
                aiohttp.client_exceptions.ClientConnectorError,
            ):
                click.echo("x", nl=False)
                had_failure = True

            await asyncio.sleep(1)
        # ensure there is a newline.
        click.echo()
        click.echo(f"Modem is back online after {time.time() - t0:.2f}s", color="green")


@click.option("-v", "--verbose", count=True)
@click.group()
def cli(verbose):
    if verbose > 0:
        import logging

        logging.basicConfig(level=logging.DEBUG)


@click.option("--dump-json/--no-dump-json", default=False)
@click.option("--dump-bbcode/--no-dump-bbcode", default=False)
@click.option("--limit", default=10)
@click.option("--remove-mac/--print-mac", default=True)
@cli.command()
def logs(
    dump_json: bool = False,
    dump_bbcode: bool = False,
    limit: int = 10,
    remove_mac: bool = False,
):
    asyncio.run(
        print_log(
            dump_json=dump_json,
            dump_bbcode=dump_bbcode,
            limit=limit,
            remove_mac=remove_mac,
        )
    )


@cli.command()
def downstreams():
    asyncio.run(print_downstreams())


@cli.command()
def upstreams():
    asyncio.run(print_upstreams())


@cli.command()
def status():
    asyncio.run(print_status())


@cli.command()
def service_flows():
    asyncio.run(print_service_flows())


@cli.command()
def reboot():
    asyncio.run(do_reboot())


if __name__ == "__main__":
    cli()
