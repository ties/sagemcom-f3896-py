import asyncio
import logging
import os
from typing import List

import aiohttp
import click
from aiohttp import web
from prometheus_async import aio
from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge, Info, Summary

from sagemcom_f3896_client.client import SagemcomModemClient, SagemcomModemSessionClient
from sagemcom_f3896_client.log_parser import (
    CMStatusMessageOFDM,
    DownstreamProfileMessage,
    ParsedMessage,
    RebootMessage,
    UpstreamProfileMessage,
)
from sagemcom_f3896_client.models import (
    ModemDownstreamChannelResult,
    ModemUpstreamChannelResult,
)
from sagemcom_f3896_client.profile_messages import ProfileMessageStore

LOG = logging.getLogger(__name__)

MODEM_METRICS_DURATION = Summary(
    "modem_metrics_processing_seconds", "Time spent processing modem metrics"
)
MODEM_UPDATE_COUNT = Counter(
    "modem_update", "Number of updates from the modem", ["status"]
)


def format_log_entries(logs: List[ParsedMessage]):
    for entry in logs:
        yield f"{' ' * 8}<tr><td>{entry.time.ctime()}</td><td>"
        if entry.priority == "error":
            yield f"<emph>{entry.priority}</emph>"
        else:
            yield entry.priority

        yield f"</td><td>{entry.message}</td></tr>"


class Exporter:
    """Prometheus export for F3896"""

    client: SagemcomModemSessionClient
    app: web.Application
    port: int

    modem_downstreams: List[ModemDownstreamChannelResult] = []
    modem_upstreams: List[ModemUpstreamChannelResult] = []

    profile_messages: ProfileMessageStore

    def __init__(self, client: SagemcomModemSessionClient, port: int):
        self.client = client
        self.app = web.Application()
        self.port = port

        self.profile_messages = ProfileMessageStore()

        self.app.add_routes(
            [
                web.get("/metrics", self.metrics),
                web.get("/", self.index),
            ]
        )

    async def run(self) -> None:
        """Start the exporter."""
        LOG.info("Starting exporter on port %d", self.port)
        runner = web.AppRunner(self.app)
        await runner.setup()
        # could also bind to a specific IP
        site = web.TCPSite(runner, None, port=self.port)

        await site.start()
        while True:
            await asyncio.sleep(3600)

    @aio.time(MODEM_METRICS_DURATION)
    async def metrics(self, _: web.Request) -> web.Response:
        """Gather metrics and return a built response"""
        registry = CollectorRegistry()
        # create metrics
        # note: _info will be postfixed
        metric_modem_info = Info("modem", "Modem information", registry=registry)
        metric_modem_uptime = Gauge("modem_uptime", "Uptime", registry=registry)

        # gather metrics in parallel
        try:
            state, system_info, _, _, _ = await asyncio.gather(
                self.client.system_state(),
                self.client.system_info(),
                self.__update_downstream_channel_metrics(registry),
                self.__update_upstream_channel_metrics(registry),
                self.__log_based_metrics(registry),
            )

            metric_modem_info.info(
                {
                    "mac": state.mac_address,
                    "serial": state.serial_number,
                    "software_version": system_info.software_version,
                    "hardware_version": system_info.hardware_version,
                    "boot_file_name": state.boot_file_name,
                }
            )
            metric_modem_uptime.set(state.up_time)
            MODEM_UPDATE_COUNT.labels(status="success").inc()
        except (
            aiohttp.ClientResponseError,
            aiohttp.client_exceptions.ClientConnectorError,
            asyncio.TimeoutError,
        ) as e:
            LOG.exception("Failed to gather metrics")
            MODEM_UPDATE_COUNT.labels(status="failed").inc()
            raise web.HTTPServiceUnavailable(
                body=f"Failed to gather metrics: {e}", headers={"Retry-After": "60"}
            )
        finally:
            # async logout so we do not block the web interface
            asyncio.create_task(self.client._logout())

        # from aiohttp support in prometheus-async
        generate, _ = aio.web._choose_generator("*/*")
        # Join the two registries
        # FIXME: Less hacky way of ensuring the content is OK
        return web.Response(
            body=generate(registry).decode("utf-8").strip()
            + "\n"
            + generate(REGISTRY).decode("utf-8")
        )

    async def __update_upstream_channel_metrics(self, registry: CollectorRegistry):
        metric_upstream_frequency = Gauge(
            "modem_upstream_frequency",
            "Upstream frequency",
            ["channel", "channel_type"],
            registry=registry,
        )
        metric_upstream_locked = Gauge(
            "modem_upstream_locked",
            "Upstream locked",
            ["channel", "channel_type"],
            registry=registry,
        )
        metric_upstream_power = Gauge(
            "modem_upstream_power",
            "Upstream power",
            ["channel", "channel_type"],
            registry=registry,
        )

        # Technically a counter, but value of a counter can not be set
        metric_upstream_timeouts = Gauge(
            "modem_upstream_timeouts",
            "Upstream timeouts by type",
            ["channel", "channel_type", "timeout_type"],
            registry=registry,
        )

        metric_upstream_atdma_info = Info(
            "modem_upstream_atdma",
            "Information on ATDMA channel",
            ["channel", "channel_type"],
            registry=registry,
        )
        metric_upstream_ofdma_info = Info(
            "modem_upstream_ofdm",
            "Information on OFDMA channel",
            ["channel", "channel_type"],
            registry=registry,
        )

        self.modem_upstreams = await self.client.modem_upstreams()
        for ch in self.modem_upstreams:
            metric_upstream_frequency.labels(
                channel=ch.channel_id, channel_type=ch.channel_type
            ).set(ch.frequency)
            metric_upstream_locked.labels(
                channel=ch.channel_id, channel_type=ch.channel_type
            ).set(1 if ch.lock_status else 0)
            metric_upstream_power.labels(
                channel=ch.channel_id, channel_type=ch.channel_type
            ).set(ch.power)

            metric_upstream_timeouts.labels(
                channel=ch.channel_id, channel_type=ch.channel_type, timeout_type="t3"
            ).set(ch.t3_timeouts)
            metric_upstream_timeouts.labels(
                channel=ch.channel_id, channel_type=ch.channel_type, timeout_type="t4"
            ).set(ch.t4_timeouts)

            match ch.channel_type:
                case "atdma":
                    metric_upstream_atdma_info.labels(
                        channel=ch.channel_id, channel_type=ch.channel_type
                    ).info(
                        {
                            "modulation": ch.modulation,
                            "symbol_rate": str(ch.symbol_rate),
                        }
                    )
                    metric_upstream_timeouts.labels(
                        channel=ch.channel_id,
                        channel_type=ch.channel_type,
                        timeout_type="t1",
                    ).set(ch.t1_timeouts)
                    metric_upstream_timeouts.labels(
                        channel=ch.channel_id,
                        channel_type=ch.channel_type,
                        timeout_type="t2",
                    ).set(ch.t2_timeouts)
                case "ofdma":
                    metric_upstream_ofdma_info.labels(
                        channel=ch.channel_id, channel_type=ch.channel_type
                    ).info(
                        {
                            "modulation": ch.modulation,
                            "channel_width_hz": str(ch.channel_width),
                            "fft_type": ch.fft_type,
                            "number_of_active_subcarriers": str(
                                ch.number_of_active_subcarriers
                            ),
                        }
                    )
                case _:
                    raise ValueError(f"Unknown channel type: {ch.channel_type}")

    async def __update_downstream_channel_metrics(
        self, registry: CollectorRegistry
    ) -> None:
        metric_downstream_frequency = Gauge(
            "modem_downstream_frequency",
            "Downstream frequency",
            ["channel", "channel_type"],
            registry=registry,
        )
        metric_downstream_rx_mer = Gauge(
            "modem_downstream_rx_mer",
            "Downstream RX MER",
            ["channel", "channel_type"],
            registry=registry,
        )
        metric_downstream_power = Gauge(
            "modem_downstream_power",
            "Downstream power",
            ["channel", "channel_type"],
            registry=registry,
        )
        metric_downstream_locked = Gauge(
            "modem_downstream_locked",
            "Downstream lock status",
            ["channel", "channel_type"],
            registry=registry,
        )

        # Technically a counter, but counter value can not be set
        metric_downstream_errors = Gauge(
            "modem_downstream_errors",
            "Downstream errors",
            ["channel", "channel_type", "error_type"],
            registry=registry,
        )

        metric_downstream_qam_snr = Gauge(
            "modem_downstream_qam_snr",
            "Downstream SNR",
            ["channel", "channel_type"],
            registry=registry,
        )
        metric_downstream_qam_info = Info(
            "modem_downstream_qam",
            "Downstream info",
            ["channel", "channel_type"],
            registry=registry,
        )

        metric_downstream_ofdm_info = Info(
            "modem_downstream_ofdm",
            "Downstream info",
            ["channel", "channel_type"],
            registry=registry,
        )

        self.modem_downstreams, primary_downstream = await asyncio.gather(
            self.client.modem_downstreams(), self.client.modem_primary_downstream()
        )

        for ch in self.modem_downstreams:
            metric_downstream_frequency.labels(
                channel=ch.channel_id, channel_type=ch.channel_type
            ).set(ch.frequency)
            metric_downstream_rx_mer.labels(
                channel=ch.channel_id, channel_type=ch.channel_type
            ).set(ch.rx_mer)
            metric_downstream_power.labels(
                channel=ch.channel_id, channel_type=ch.channel_type
            ).set(ch.power)
            metric_downstream_locked.labels(
                channel=ch.channel_id,
                channel_type=ch.channel_type,
            ).set(ch.lock_status)

            metric_downstream_errors.labels(
                channel=ch.channel_id,
                channel_type=ch.channel_type,
                error_type="corrected",
            ).set(ch.corrected_errors)
            metric_downstream_errors.labels(
                channel=ch.channel_id,
                channel_type=ch.channel_type,
                error_type="uncorrected",
            ).set(ch.uncorrected_errors)

            match ch.channel_type:
                case "sc_qam":
                    metric_downstream_qam_snr.labels(
                        channel=ch.channel_id, channel_type=ch.channel_type
                    ).set(ch.snr)
                    metric_downstream_qam_info.labels(
                        channel=ch.channel_id,
                        channel_type=ch.channel_type,
                    ).info(
                        {
                            "modulation": ch.modulation,
                            "primary": "true"
                            if ch.channel_id == primary_downstream.channel_id
                            else "false",
                        }
                    )
                case "ofdm":
                    metric_downstream_ofdm_info.labels(
                        channel=ch.channel_id, channel_type=ch.channel_type
                    ).info(
                        {
                            "modulation": ch.modulation,
                            "channel_width_hz": str(ch.channel_width),
                            "fft_type": ch.fft_type,
                            "number_of_active_subcarriers": str(
                                ch.number_of_active_subcarriers
                            ),
                        }
                    )
                case _:
                    raise ValueError("Unknown downstream type %s" % ch.channel_type)

    async def __log_based_metrics(self, registry: CollectorRegistry) -> None:
        """
        Gather metrics from the logs.

        This goes through some pain to keep all profile messages for channels that are still present. There are two reasons:
          * The modem expires log entries after enough have been produced. The downstream message is rare in known setups, so that ends to be no longer be present otherwise.
          * We do not use the regular registry, and using that would mean explicitly deleting no longer present channels their profile
        """
        metric_channel_profile = Gauge(
            "modem_channel_profile",
            "Profile assigned to channel",
            ["direction", "channel_id", "slot"],
            registry=registry,
        )
        metric_ds_ofdm_profile_failure = Gauge(
            "modem_cmstatus_info",
            "FEC errors were over limit on one of the assigned downstream OFDM profiles of a channel",
            ["channel_id", "profile", "type"],
            registry=registry,
        )
        # Actually a Counter, but Counter would get a non-sensical (beccuse we recreate every request)
        # _created metric.
        metric_log_reboots = Gauge(
            "modem_reboot_count",
            "Number of reboots in modem log",
            registry=registry,
        )
        metric_log_by_priority = Gauge(
            "modem_log_count", "Number of log messages", ["priority"], registry=registry
        )

        log_lines = await self.client.modem_event_log()
        for line in log_lines:
            metric_log_by_priority.labels(priority=line.priority).inc()
        # parse the log lines
        log_messages = [line.parse() for line in reversed(log_lines)]

        # count reboots and find the last, so we only parse messages
        # that apply to this power cycle.
        last_reboot_idx = 0
        for idx, message in enumerate(log_messages):
            match message:
                case RebootMessage(reason=_):
                    metric_log_reboots.inc()
                    last_reboot_idx = idx

        for message in log_messages[last_reboot_idx:]:
            # Process the first downstream and upstream messages
            match message:
                case CMStatusMessageOFDM(
                    channel_id=channel_id,
                    ds_id=_,
                    event_code=event_code,
                    profile=profile,
                ):
                    if event_code in (16, 24):
                        value = 1 if event_code == 16 else 0

                        metric_ds_ofdm_profile_failure.labels(
                            channel_id=channel_id,
                            profile=profile,
                            type="ofdm_profile_failure",
                        ).set(value)
                case DownstreamProfileMessage():
                    self.profile_messages.add(message)
                case UpstreamProfileMessage():
                    self.profile_messages.add(message)

        self.profile_messages.update_for_channels(
            self.modem_downstreams, self.modem_upstreams
        )

        for message in self.profile_messages:
            match message:
                case DownstreamProfileMessage(
                    channel_id=channel_id,
                    previous_profile=_,
                    profile=profile,
                ):
                    for idx, profile in enumerate(profile):
                        metric_channel_profile.labels(
                            direction="downstream",
                            channel_id=channel_id,
                            slot=str(idx + 1),
                        ).set(profile)
                case UpstreamProfileMessage(
                    channel_id=channel_id,
                    previous_profile=_,
                    profile=profile,
                ):
                    for idx, profile in enumerate(profile):
                        metric_channel_profile.labels(
                            direction="upstream",
                            channel_id=channel_id,
                            slot=str(idx + 1),
                        ).set(profile)

    async def index(self, _: web.Request) -> str:
        """Serve an index page."""
        logs = await self.client.modem_event_log()

        return web.Response(
            text=f"""<html>
            <head><title>Sagemcom F3896</title></head>
            <style>
                body {{
                    font-family: helvetica, arial, sans-serif;
                }}

                emph {{
                    font-weight: bold;
                }}

                table {{
                    font-size: 75%;
                }}

                thead td {{
                    font-weight: bold;
                    padding: 0.5em;
                }}

                td {{
                    padding: 0 0.5em;
                }}
            </style>
            <body>
                <h1>SagemCom F3896</h1>
                <p><a href="/metrics">Metrics</a></p>
                <p>
                <table>
                    <thead>
                    <tr><td>Time</td><td>Priority</td><td>Message</td></tr>
                    </thread>
                    <tbody>
                    {''.join(list(format_log_entries(logs)))}
                    </tbody>
                </table>
                </p>
                <p>
                    <small>F3896 exporter <a href="https://github.com/ties/sagemcom-f3896-py">github.com/ties/sagemcom-f3896-py</a></small>
                </p>
            </body>
        </html>""",
            content_type="text/html",
        )


@click.command()
@click.option("-v", "--verbose", count=True)
@click.option(
    "-u",
    "--base-url",
    default=os.environ.get("MODEM_URL", "http://192.168.100.1"),
    help="URL to modem - default from MODEM_URL",
)
@click.option("-p", "--port", default=8080, help="Port to listen on")
@click.option(
    "--password",
    default=os.environ.get("MODEM_PASSWORD", ""),
    help="Password - default from MODEM_PASSWORD",
)
def main(verbose, port: int, password: str, base_url: str):
    asyncio.run(async_main(verbose, port, password, base_url))


async def async_main(verbose, port: int, password: str, base_url: str):
    if verbose > 0:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    async with SagemcomModemClient(base_url, password) as client:
        exporter = Exporter(client, port)
        await exporter.run()


if __name__ == "__main__":
    main()
