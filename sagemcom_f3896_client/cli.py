import asyncio
import datetime
import math
import time
import aiohttp

import click

from sagemcom_f3896_client.util import build_client

async def print_downstreams():
    async with build_client() as client:
        for ch in await client.modem_downstreams():
            lock_status = "locked" if ch.lock_status else "unlocked"
            match ch.channel_type:
                case "sc_qam":
                    click.echo(f"{ch.channel_type:<6} {ch.channel_id:>3} {ch.frequency:>8} {ch.power:>4} {ch.snr:>9} {ch.modulation:>8} {ch.rx_mer/1.0:>4} {lock_status:>8} {ch.corrected_errors:>10} {ch.uncorrected_errors:>3}")
                case "ofdm":
                    click.echo(click.style(f"{ch.channel_type:<6}", fg="green") + f" {ch.channel_id:>3} {ch.frequency:>8} {ch.power:>4} {ch.channel_width:>9} {ch.modulation:>8} {ch.rx_mer:>4} {lock_status :>8} {ch.fft_type:>3} {ch.number_of_active_subcarriers:>4} {ch.corrected_errors:>10} {ch.uncorrected_errors:>3}")

async def print_upstreams():
    async with build_client() as client:
        for ch in await client.modem_upstreams():
            lock_status = "locked" if ch.lock_status else "unlocked"
            match ch.channel_type:
                case "atdma":
                    click.echo(f"{ch.channel_type:<6} {ch.channel_id:>2} {ch.frequency:>8} {round(ch.power, 1):>4} {ch.symbol_rate:>5} {ch.modulation:>6} {lock_status:>8} {ch.t1_timeouts:>2} {ch.t2_timeouts:>2} {ch.t3_timeouts:>2} {ch.t4_timeouts:>2}")
                case "ofdma":
                    click.echo(click.style(f"{ch.channel_type:<6}", fg="green") + f" {ch.channel_id:>2} {ch.frequency:>8} {round(ch.power, 1):>4} {ch.channel_width:>5} {ch.modulation:>6} {lock_status:>8} {ch.number_of_active_subcarriers:>4} {ch.fft_type:>4} {ch.t3_timeouts:>2} {ch.t4_timeouts:>2}")

async def print_log():
    async with build_client() as client:
        for entry in await client.modem_event_log():
            match entry.priority:
                case "critical":
                    priority = click.style(f"{entry.priority:<9}", fg="red", bold=True)
                case "error":
                    priority = click.style(f"{entry.priority:<9}", fg="red")
                case "notice":
                    priority = click.style(f"{entry.priority:<9}", fg="green")
                case _:
                    priority = entry.priority

            click.echo(f"{entry.time.ctime()} {priority} {entry.message}")

async def print_status():
    async with build_client() as client:
        status = await client.system_state()
        system_info = await client.system_info()
        click.echo(f"| ---------------- | ---------------------------- |")
        click.echo(f"| Model            | {system_info.model_name:>28} |")
        click.echo(f"| MAC address      | {status.mac_address:>28} |")
        click.echo(f"| Serial number    | {status.serial_number:>28} |")
        click.echo(f"| Hardware version | {system_info.hardware_version:>28} |")
        click.echo(f"| Software version | {system_info.software_version:>28} |")
        uptime = datetime.timedelta(seconds=status.up_time)
        click.echo(f"| Uptime           | {str(uptime):>28} |")
        click.echo(f"| Boot file        | {status.boot_file_name:>28} |")
        click.echo(f"| DOCSIS version   | {status.docsis_version:>28} |")
        click.echo(f"| Status           | {status.status:>28} |")
        click.echo(f"| Max CPEs         | {status.max_cpes:>28} |")
        click.echo(f"| Access allowed   | {status.access_allowed:>28} |")
        click.echo(f"| ---------------- | ---------------------------- |")

async def do_reboot():
    t0 = time.time()
    click.echo("Rebooting modem...", color="red")
    async with build_client(timeout=30) as client:
        await client.system_reboot()
    click.echo(f"Modem rebooted in {time.time()-t0:.2f}s", color="green")
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
            except (asyncio.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
                click.echo("x", nl=False)
                had_failure = True

            await asyncio.sleep(1)
        # ensure there is a newline.
        click.echo()
        click.echo(f"Modem is back online after {time.time()-t0:.2f}s", color="green")

    

@click.option("-v", "--verbose", count=True)
@click.group()
def cli(verbose):
    if verbose > 0:
        import logging
        logging.basicConfig(level=logging.DEBUG)

@cli.command()
def log():
    asyncio.run(print_log())

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
def reboot():
    asyncio.run(do_reboot())


if __name__ == '__main__':
    cli()
