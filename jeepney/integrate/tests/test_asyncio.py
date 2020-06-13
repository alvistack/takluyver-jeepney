import pytest

from jeepney.integrate.asyncio import connect_and_authenticate
from .utils import have_session_bus

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        not have_session_bus, reason="Tests require DBus session bus"
    ),
]

async def test_connect():
    transport, proto = await connect_and_authenticate(bus='SESSION')
    assert proto.unique_name.startswith(':')
