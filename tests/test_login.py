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


@requires_modem_password()
@pytest.mark.asyncio
async def test_create_tokens__not_logged_in(caplog):
    caplog.set_level(logging.DEBUG)

    client_wrapper = build_client()
    async with client_wrapper as client:
        # static user id used on Ziggo variety of modem
        token = await client.user_tokens(3, client.password)

        assert token.token is not None


@requires_modem_password()
@pytest.mark.asyncio
async def test_create_tokens__logged_in(caplog):
    caplog.set_level(logging.DEBUG)

    client_wrapper = build_client()
    async with client_wrapper as client:
        await client._login()
        LOG.debug("Token: %s", client.authorization.token)
        # static user id used on Ziggo variety of modem
        token = await client.user_tokens(3, client.password)
        LOG.debug("New token: %s", client.authorization.token)

        assert client.authorization.token == token.token

        # do an authenticated call
        res = await client.system_info()
        assert res is not None
