import pytest

from jeepney.integrate.trio import open_dbus_connection
from .utils import have_session_bus

pytestmark = [
    pytest.mark.trio,
    pytest.mark.skipif(
        not have_session_bus, reason="Tests require DBus session bus"
    ),
]

async def test_connect():
    conn = await open_dbus_connection(bus='SESSION')
    async with conn:
        assert conn.unique_name.startswith(':')
