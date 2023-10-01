import asyncio
import math

import click

from sagemcom_f3896_client.util import build_client

async def print_downstreams():
    async with build_client() as client:
        for ch in await client.modem_downstreams():
            lock_status = "locked" if ch.lock_status else "unlocked"
            match ch.channel_type:
                case "sc_qam":
                    click.echo(f"{ch.channel_type:<6} {ch.channel_id:>3} {ch.modulation:>8} {ch.frequency:>6} {ch.snr:>8} {ch.power:>4} {ch.rx_mer:>4} {lock_status:>8} {ch.corrected_errors:>10} {ch.uncorrected_errors:>3}")
                case "ofdm":
                    click.echo(click.style(f"{ch.channel_type:<6}", fg="green") + f" {ch.channel_id:>3} {ch.modulation:>8} {ch.channel_width:>6} {ch.fft_type:>3} {ch.number_of_active_subcarriers:>4} {ch.power:>4} {ch.rx_mer:>4} {lock_status :>8} {ch.corrected_errors:>10} {ch.uncorrected_errors:>3}")

async def print_upstreams():
    async with build_client() as client:
        for ch in await client.modem_upstreams():
            lock_status = "locked" if ch.lock_status else "unlocked"
            match ch.channel_type:
                case "atdma":
                    click.echo(f"{ch.channel_type:<6} {ch.channel_id:>2} {lock_status:>8} {round(ch.power, 1):>4} {ch.modulation:>6} {ch.frequency:>6} {ch.symbol_rate:>5} {ch.t1_timeouts:>2} {ch.t2_timeouts:>2} {ch.t3_timeouts:>2} {ch.t4_timeouts:>2}")
                case "ofdma":
                    click.echo(f"{ch.channel_type:<6} {ch.channel_id:>2} {lock_status:>8} {round(ch.power, 1):>4} {ch.modulation:>6} {ch.channel_width:>5} {ch.fft_type:>4} {ch.number_of_active_subcarriers:>4} {ch.first_active_subcarrier:>4} {ch.t3_timeouts:>2} {ch.t4_timeouts:>2}")

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


if __name__ == '__main__':
    cli()