import secrets

import pytest


@pytest.fixture
def random_app_label():
    return f"app_{secrets.token_hex(4)}"
