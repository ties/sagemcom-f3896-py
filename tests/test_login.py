import logging

import pytest

from sagemcom_f3896_client.util import build_client
from tests.util import requires_modem_password

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

@requires_modem_password()
@pytest.mark.asyncio
async def test_login_logout(caplog):
    caplog.set_level(logging.DEBUG)

    async with build_client() as client:
        await client._login()
        assert client.authorization.token is not None
