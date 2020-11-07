import trio
import pytest

from jeepney import DBusAddress, DBusErrorResponse, MessageType, new_method_call
from jeepney.bus_messages import message_bus
from jeepney.io.trio import (
    open_dbus_connection, open_dbus_router, Proxy,
)
from .utils import have_session_bus

pytestmark = [
    pytest.mark.trio,
    pytest.mark.skipif(
        not have_session_bus, reason="Tests require DBus session bus"
    ),
]

# Can't use any async fixtures here, because pytest-asyncio tries to handle
# all of them: https://github.com/pytest-dev/pytest-asyncio/issues/124

async def test_connect():
    conn = await open_dbus_connection(bus='SESSION')
    async with conn:
        assert conn.unique_name.startswith(':')

bus_peer = DBusAddress(
    bus_name='org.freedesktop.DBus',
    object_path='/org/freedesktop/DBus',
    interface='org.freedesktop.DBus.Peer'
)

async def test_send_and_get_reply():
    ping_call = new_method_call(bus_peer, 'Ping')
    async with open_dbus_router(bus='SESSION') as req:
        with trio.fail_after(5):
            reply = await req.send_and_get_reply(ping_call)

    assert reply.header.message_type == MessageType.method_return
    assert reply.body == ()


async def test_send_and_get_reply_error():
    ping_call = new_method_call(bus_peer, 'Snart')  # No such method
    async with open_dbus_router(bus='SESSION') as req:
        with trio.fail_after(5):
            reply = await req.send_and_get_reply(ping_call)

    assert reply.header.message_type == MessageType.error


async def test_proxy():
    async with open_dbus_router(bus='SESSION') as req:
        proxy = Proxy(message_bus, req)
        name = "io.gitlab.takluyver.jeepney.examples.Server"
        res = await proxy.RequestName(name)
        assert res in {(1,), (2,)}  # 1: got the name, 2: queued

        has_owner, = await proxy.NameHasOwner(name)
        assert has_owner is True


async def test_proxy_error():
    async with open_dbus_router(bus='SESSION') as req:
        proxy = Proxy(message_bus, req)
        with pytest.raises(DBusErrorResponse):
            await proxy.RequestName(":123")  # Invalid name
