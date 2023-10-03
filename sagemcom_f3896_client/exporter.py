import asyncio
import click
import logging
import os

from aiohttp import web
from prometheus_async import aio
from prometheus_client import REGISTRY, CollectorRegistry, Gauge, Info, Summary

from sagemcom_f3896_client.client import SagemcomModemClient, SagemcomModemSessionClient


LOG = logging.getLogger(__name__)

MODEM_METRICS_DURATION = Summary('modem_metrics_processing_seconds', 'Time spent processing modem metrics')
        

class Exporter:
    client: SagemcomModemSessionClient
    app: web.Application
    port: int

    def __init__(self, client: SagemcomModemSessionClient, port: int):
        self.client = client
        self.app = web.Application()
        self.port = port

        self.app.add_routes(
            [
                web.get("/metrics", self.metrics),
                web.get("/", self.index),
            ]
        )

    async def run(self) -> None:
        LOG.info("Starting exporter on port %d", self.port)
        runner = web.AppRunner(self.app)
        await runner.setup()
        # could also bind to a specific IP
        site = web.TCPSite(runner, None, port=self.port)

        await site.start()
        while True:
            await asyncio.sleep(3600)

    @aio.time(MODEM_METRICS_DURATION)
    async def metrics(self, req: web.Request) -> web.Response:
        """Gather metrics and return a built response"""
        registry = CollectorRegistry()
        # create metrics
        metric_modem_info = Info("modem_info", "Modem information", registry=registry)
        metric_modem_uptime = Gauge("modem_uptime", "Uptime", registry=registry)

        metric_upstream_frequency = Gauge("modem_upstream_frequency", "Upstream frequency", ["channel", "channel_type"], registry=registry)
        metric_upstream_locked = Gauge("modem_upstream_locked", "Upstream locked", ["channel", "channel_type"], registry=registry)
        metric_upstream_power = Gauge("modem_upstream_power", "Upstream power", ["channel", "channel_type"], registry=registry)

        metric_upstream_timeouts = Gauge("modem_upstream_timeouts", "Upstream timeouts by type", ["channel", "channel_type", "timeout_type"], registry=registry)

        metric_upstream_atdma_info = Info("modem_upstream_atdma", "Information on ATDMA channel", ["channel", "channel_type"], registry=registry)
        metric_upstream_ofdma_info = Info("modem_upstream_ofdm", "Information on OFDMA channel", ["channel", "channel_type"], registry=registry)


        metric_downstream_frequency = Gauge("modem_downstream_frequency", "Downstream frequency", ["channel", "channel_type"], registry=registry)
        metric_downstream_rx_mer = Gauge("modem_downstream_rx_mer", "Downstream RX MER", ["channel", "channel_type"], registry=registry)
        metric_downstream_power = Gauge("modem_downstream_power", "Downstream power", ["channel", "channel_type"], registry=registry)
        metric_downstream_locked = Gauge("modem_downstream_locked", "Downstream lock status", ["channel", "channel_type"], registry=registry)
        
        metric_downstream_errors = Gauge("modem_downstream_errors", "Downstream errors", ["channel", "channel_type", "error_type"], registry=registry)

        metric_downstream_qam_snr = Gauge("modem_downstream_qam_snr", "Downstream SNR", ["channel", "channel_type"], registry=registry)
        metric_downstream_qam_info = Info("modem_downstream_qam_info", "Downstream info", ["channel", "channel_type"], registry=registry)

        metric_downstream_ofdm_info = Info("modem_downstream_ofdm_info", "Downstream info", ["channel", "channel_type"], registry=registry)

        # gather metrics in parallel
        state, system_info, downstreams, upstreams = await asyncio.gather(
            self.client.system_state(),
            self.client.system_info(),
            self.client.modem_downstreams(),
            self.client.modem_upstreams(),
        )
        # async logout so we do not block the web interface
        asyncio.create_task(self.client._logout())

        metric_modem_info.info({"mac": state.mac_address, "serial": state.serial_number, "software_version": system_info.software_version, "hardware_version": system_info.hardware_version, "boot_file_name": state.boot_file_name})
        metric_modem_uptime.set(state.up_time)

        for ch in upstreams:
            metric_upstream_frequency.labels(channel=ch.channel_id, channel_type=ch.channel_type).set(ch.frequency)
            metric_upstream_locked.labels(channel=ch.channel_id, channel_type=ch.channel_type).set(1 if ch.lock_status else 0)
            metric_upstream_power.labels(channel=ch.channel_id, channel_type=ch.channel_type).set(ch.power)

            metric_upstream_timeouts.labels(channel=ch.channel_id, channel_type=ch.channel_type, timeout_type="t3").set(ch.t3_timeouts)
            metric_upstream_timeouts.labels(channel=ch.channel_id, channel_type=ch.channel_type, timeout_type="t4").set(ch.t4_timeouts)

            match ch.channel_type:
                case "atdma":
                    metric_upstream_atdma_info.labels(channel=ch.channel_id, channel_type=ch.channel_type).info({"modulation": ch.modulation, "symbol_rate": str(ch.symbol_rate)})
                    metric_upstream_timeouts.labels(channel=ch.channel_id, channel_type=ch.channel_type, timeout_type="t1").set(ch.t1_timeouts)
                    metric_upstream_timeouts.labels(channel=ch.channel_id, channel_type=ch.channel_type, timeout_type="t2").set(ch.t2_timeouts)
                case "ofdma":
                    metric_upstream_ofdma_info.labels(channel=ch.channel_id, channel_type=ch.channel_type).info({"modulation": ch.modulation, "channel_width_hz": str(ch.channel_width), "fft_type": ch.fft_type, "number_of_active_subcarriers": str(ch.number_of_active_subcarriers)})
                case _:
                    raise ValueError("Unknown channel type: %s" % ch.channel_type)
                

        for ch in downstreams:
            metric_downstream_frequency.labels(channel=ch.channel_id, channel_type=ch.channel_type).set(ch.frequency)
            metric_downstream_rx_mer.labels(channel=ch.channel_id, channel_type=ch.channel_type).set(ch.rx_mer)
            metric_downstream_power.labels(channel=ch.channel_id, channel_type=ch.channel_type).set(ch.power)
            metric_downstream_locked.labels(channel=ch.channel_id, channel_type=ch.channel_type).set(ch.lock_status)

            metric_downstream_errors.labels(channel=ch.channel_id, channel_type=ch.channel_type, error_type="corrected").set(ch.corrected_errors)
            metric_downstream_errors.labels(channel=ch.channel_id, channel_type=ch.channel_type, error_type="uncorrected").set(ch.uncorrected_errors)

            match ch.channel_type:
                case "sc_qam":
                    metric_downstream_qam_snr.labels(channel=ch.channel_id, channel_type=ch.channel_type).set(ch.snr)
                    metric_downstream_qam_info.labels(channel=ch.channel_id, channel_type=ch.channel_type).info({"modulation": ch.modulation})
                case "ofdm":
                    metric_downstream_ofdm_info.labels(channel=ch.channel_id, channel_type=ch.channel_type).info({"modulation": ch.modulation, "channel_width_hz": str(ch.channel_width), "fft_type": ch.fft_type, "number_of_active_subcarriers": str(ch.number_of_active_subcarriers)})
                case _:
                    raise ValueError("Unknown downstream type %s" % ch.channel_type)
                
        # from aiohttp support in prometheus-async
        generate, content_type = aio.web._choose_generator(req.headers.get("Accept"))
        # Join the two registries
        resp = web.Response(body=generate(registry) + generate(REGISTRY))
        resp.content_type = content_type
        return resp

    async def index(self, req) -> str:
        logs = await self.client.modem_event_log()

        return web.Response(
            text=f"""<html>
            <head><title>Sagemcom F3896</title></head>
            <body>
                <h1>SagemCom F3896</h1>
                <p><a href="/metrics">Metrics</a></p>
                <p>
                <table>
                    <thead>
                    <tr><td>Time</td><td>Priority</td><td>Message</td></tr>
                    </thread>
                    <tbody>
                    {''.join(
                        [
                            f"<tr><td>{entry.time.ctime()}</td><td>{entry.priority}</td><td>{entry.message}</td></tr>"
                            for entry in logs
                        ]
                    )}
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
@click.option("-u", "--base-url", default=os.environ.get("MODEM_URL", "http://192.168.100.1"), help="URL to modem - default from MODEM_URL")
@click.option("-p", "--port", default=8080, help="Port to listen on")
@click.option("--password", default=os.environ.get("MODEM_PASSWORD", ""), help="Password - default from MODEM_PASSWORD")
def main(verbose,  port: int, password: str, base_url: str):
    asyncio.run(async_main(verbose, port, password, base_url))

async def async_main(verbose,  port: int, password: str, base_url: str):
    if verbose > 0:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    async with SagemcomModemClient(base_url, password) as client:
        exporter = Exporter(client, port)
        await exporter.run()

if __name__ == '__main__':
    main()
