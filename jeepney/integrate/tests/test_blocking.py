import pytest

from jeepney import new_method_call, MessageType, DBusAddress
from jeepney.bus_messages import message_bus
from jeepney.integrate.blocking import connect_and_authenticate, Proxy
from .utils import have_session_bus

pytestmark = pytest.mark.skipif(
    not have_session_bus, reason="Tests require DBus session bus"
)

@pytest.fixture
def session_conn():
    with connect_and_authenticate(bus='SESSION') as conn:
        yield conn


def test_connect(session_conn):
    assert session_conn.unique_name.startswith(':')

bus_peer = DBusAddress(
    bus_name='org.freedesktop.DBus',
    object_path='/org/freedesktop/DBus',
    interface='org.freedesktop.DBus.Peer'
)

def test_send_and_get_reply(session_conn):
    ping_call = new_method_call(bus_peer, 'Ping')
    reply = session_conn.send_and_get_reply(ping_call, timeout=5, unwrap=False)
    assert reply.header.message_type == MessageType.method_return
    assert reply.body == ()

    ping_call = new_method_call(bus_peer, 'Ping')
    reply_body = session_conn.send_and_get_reply(ping_call, timeout=5, unwrap=True)
    assert reply_body == ()

def test_proxy(session_conn):
    proxy = Proxy(message_bus, session_conn, timeout=5)
    name = "io.gitlab.takluyver.jeepney.examples.Server"
    res = proxy.RequestName(name)
    assert res in {(1,), (2,)}  # 1: got the name, 2: queued

    has_owner, = proxy.NameHasOwner(name)
    assert has_owner is True
