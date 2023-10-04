import asyncio

import pytest

from sagemcom_f3896_client.client import SagemcomModemClient


@pytest.mark.asyncio
async def test_connect_non_existent_host():
    """Connect to a non-responding IP and ensure we observe the timeout."""
    with pytest.raises(asyncio.TimeoutError):
        async with SagemcomModemClient(
            "http://192.0.2.0", "DEADBEEF", timeout=0.1
        ) as client:
            await client.modem_downstreams()


@pytest.mark.asyncio
async def test_connect_non_existent_host__login_required():
    """Connect to a non-responding IP and ensure we observe the timeout."""
    with pytest.raises(asyncio.TimeoutError):
        async with SagemcomModemClient(
            "http://192.0.2.0", "DEADBEEF", timeout=0.1
        ) as client:
            # unreachable IP so this is safe
            await client.system_reboot()
