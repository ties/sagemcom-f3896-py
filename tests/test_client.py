import collections
import datetime
import logging
import os
import random

import aiohttp
import pytest
from pytest import LogCaptureFixture

from sagemcom_f3896_client import SagemcomModemSessionClient
from tests.util import requires_modem_password

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)


@pytest.fixture
def client(event_loop):
    """
    Build a client using settings from environment variable, without requiring a context manager.
    """
    modem_url = os.environ.get("MODEM_URL", None)
    if not modem_url:
        LOG.info("MODEM_URL environment variable is not set, using default")
        modem_url = "http://192.168.100.1"

    modem_password = os.environ.get("MODEM_PASSWORD")
    assert modem_password, "MODEM_PASSWORD environment variable is not set"

    async def sessio():
        return aiohttp.ClientSession()

    session = event_loop.run_until_complete(sessio())
    client = SagemcomModemSessionClient(session, modem_url, modem_password)
    yield client

    event_loop.run_until_complete(client._logout())

@requires_modem_password()
@pytest.mark.asyncio
async def test_echo(
    client: SagemcomModemSessionClient, caplog: LogCaptureFixture
):
    caplog.set_level(logging.DEBUG)

    randint = random.randint(0, 1_000_000)

    echoed = await client.echo({"value": randint})
    assert echoed["value"] == randint


@requires_modem_password()
@pytest.mark.asyncio
async def test_modem_state(
    client: SagemcomModemSessionClient, caplog: LogCaptureFixture
):
    caplog.set_level(logging.DEBUG)

    state = await client.system_state()
    assert state.up_time > 0
    assert state.status == "operational"


@requires_modem_password()
@pytest.mark.asyncio
async def test_event_log(client: SagemcomModemSessionClient, caplog: LogCaptureFixture):
    caplog.set_level(logging.DEBUG)

    log_elements = await client.modem_event_log()

    cnt = collections.Counter([elem.priority for elem in log_elements])
    assert cnt["notice"] + cnt["error"] + cnt["warning"] + cnt["critical"] == len(
        log_elements
    )

    now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)

    for elem in log_elements:
        # assume all log elements are less than a year old
        assert (now - elem.time) < datetime.timedelta(days=365)


@requires_modem_password()
@pytest.mark.asyncio
async def test_modem_service_flows(
    client: SagemcomModemSessionClient, caplog: LogCaptureFixture
):
    caplog.set_level(logging.DEBUG)

    flows = await client.modem_service_flows()

    for flow in flows:
        assert flow.id > 0
        assert flow.direction is not None
        assert flow.max_traffic_rate > 0
        assert flow.max_traffic_burst >= 0
        assert flow.max_concatenated_burst >= 0
        assert flow.min_reserved_rate >= 0
        assert flow.schedule_type is not None


@requires_modem_password()
@pytest.mark.asyncio
async def test_modem_downstreams(
    client: SagemcomModemSessionClient, caplog: LogCaptureFixture
):
    caplog.set_level(logging.DEBUG)

    downstreams = await client.modem_downstreams()

    for ds in downstreams:
        assert ds.rx_mer > 0 and ds.rx_mer < 100
        assert ds.power >= -5
        assert ds.lock_status is not None
        assert ds.corrected_errors >= 0
        assert ds.uncorrected_errors >= 0
        assert ds.channel_id > 0

        match ds.channel_type:
            case "sc_qam":
                assert ds.frequency > 10_000_000 and ds.frequency < 1_000_000_000
                assert ds.snr > 0
                assert ds.modulation in ("qam_256",)
            case "ofdm":
                # in mhz
                assert ds.channel_width > 1_000_000 and ds.channel_width < 170_000_000
                assert ds.fft_type in ("2K", "4K", "8K", "16K")
                assert ds.number_of_active_subcarriers > 0
                assert ds.modulation in (
                    "qam_4096",
                    "qam_2048",
                    "qam_1024",
                    "qam_512",
                    "qam_256",
                )
            case _:
                raise ValueError(f"unknown channel_type: {ds.channel_type}")


@requires_modem_password()
@pytest.mark.asyncio
async def test_modem_upstreams(
    client: SagemcomModemSessionClient, caplog: LogCaptureFixture
):
    caplog.set_level(logging.DEBUG)

    upstreams = await client.modem_upstreams()

    for us in upstreams:
        assert us.channel_id > 0
        assert us.frequency > 10_000_000 and us.frequency < 1_000_000_000
        assert us.lock_status is not None
        assert us.power > -50 and us.power < 50
        assert us.modulation in ("qam_64", "qam_256")

        assert us.t3_timeouts >= 0
        assert us.t4_timeouts >= 0

        match us.channel_type:
            case "atdma":
                assert us.symbol_rate > 0 and us.symbol_rate <= 10240
                assert us.t1_timeouts >= 0
                assert us.t2_timeouts >= 0
            case "ofdma":
                assert us.channel_width > 2 and us.channel_width < 200
                assert us.fft_type in ("4K", "2K")
                assert us.number_of_active_subcarriers > 0
            case _:
                raise ValueError(f"unknown channel_type: {us.channel_type}")
            

@requires_modem_password()
@pytest.mark.asyncio
async def test_system_info(
    client: SagemcomModemSessionClient, caplog: pytest.LogCaptureFixture
):
    caplog.set_level(logging.DEBUG)

    info = await client.system_info()
    assert "F3896" in info.model_name


@requires_modem_password()
@pytest.mark.asyncio
async def test_system_provisioning(
    client: SagemcomModemSessionClient, caplog: pytest.LogCaptureFixture
):
    caplog.set_level(logging.DEBUG)

    provision_status = await client.system_provisioning()
    assert provision_status.provisioning_mode == "disable"
    assert len(list(filter(":".__eq__, provision_status.mac_address))) == 5
