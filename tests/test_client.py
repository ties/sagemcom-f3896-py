import asyncio
import aiohttp

import logging
import os
import pytest

from sagemcom_f3896 import SagemcomModemSessionClient

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)


@pytest.fixture
def client(event_loop):
    """
    Build a client using settings from environment variable, without requiring a context manager.
    """
    modem_url = os.environ.get('MODEM_URL', None)
    if not modem_url:
        LOG.info('MODEM_URL environment variable is not set, using default')
        modem_url = 'http://192.168.100.1'

    modem_password = os.environ.get('MODEM_PASSWORD')
    assert modem_password, 'MODEM_PASSWORD environment variable is not set'

    async def sessio():
        return aiohttp.ClientSession()

    session = event_loop.run_until_complete(sessio())
    return SagemcomModemSessionClient(session, modem_url, modem_password)


@pytest.mark.asyncio
async def test_system_info(client: SagemcomModemSessionClient, caplog):
    caplog.set_level(logging.DEBUG)

    info = await client.system_info()
    assert 'F3896' in info.model_name

    LOG.debug(info)


@pytest.mark.asyncio
async def test_modem_state(client: SagemcomModemSessionClient, caplog):
    caplog.set_level(logging.DEBUG)

    state = await client.system_state()
    assert state.up_time > 0
    assert state.status == 'operational'

    LOG.debug(state)
