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
            await client.system_info()
