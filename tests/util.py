
import os
import pytest


def requires_modem_password():
    return pytest.mark.skipif(
        not os.environ.get("MODEM_PASSWORD", False),
        reason=f"MODEM_PASSWORD environment variable not set which is needed for integration tests."
    )