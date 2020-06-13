import pytest

from jeepney.integrate.blocking import connect_and_authenticate
from .utils import have_session_bus

pytestmark = pytest.mark.skipif(
    not have_session_bus, reason="Tests require DBus session bus"
)

def test_connect():
    with connect_and_authenticate(bus='SESSION') as conn:
        assert conn.unique_name.startswith(':')
