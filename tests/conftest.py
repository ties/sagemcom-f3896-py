import logging
import os

import aiohttp
import pytest

from sagemcom_f3896_client.client import SagemcomModemSessionClient

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
