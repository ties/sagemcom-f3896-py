import logging
import os

from sagemcom_f3896_client import SagemcomModemClient

LOG = logging.getLogger(__name__)


def build_client(*args, **kwargs):
    modem_url = os.environ.get("MODEM_URL", None)
    if not modem_url:
        LOG.debug("MODEM_URL environment variable is not set, using default")
        modem_url = "http://192.168.100.1"

    modem_password = os.environ.get("MODEM_PASSWORD")
    assert modem_password, "MODEM_PASSWORD environment variable is not set"

    return SagemcomModemClient(modem_url, modem_password, *args, **kwargs)
