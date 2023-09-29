import logging
import os
import pytest

from sagemcom_f3896.util import build_client

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_login_logout(caplog):
    caplog.set_level(logging.DEBUG)

    async with build_client() as client:
        await client._login()
        LOG.info(client.authorization)
        assert client.authorization.token is not None
