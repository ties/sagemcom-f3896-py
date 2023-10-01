import asyncio
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

async def do_reboot():
    async with build_client(timeout=1) as client:
        click.echo("Rebooting modem...", color="red")
        t0 = time.time()
        try:
            await client.system_reboot()
        except asyncio.TimeoutError:
            # sporadically happens to reboot before sending response
            pass
        had_failure = False

        width = 0
        while True:
            try:
                res = await client.echo({"ping": True})
                width += 1
                click.echo(".", nl=width % 80 == 0)
                if had_failure:
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
def reboot():
    asyncio.run(do_reboot())


if __name__ == '__main__':
    cli()
