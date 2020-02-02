from collections import OrderedDict
from outcome import Value, Error
import trio
from trio import (
    open_unix_socket, open_memory_channel, open_nursery,
    Cancelled, CancelScope, Event, SocketStream, EndOfChannel, Nursery
)
from trio.abc import Channel

from jeepney.auth import SASLParser, make_auth_external, BEGIN, AuthenticationError
from jeepney.bus import get_bus
from jeepney.low_level import Parser, MessageType, HeaderFields
from jeepney.wrappers import ProxyBase
from jeepney.bus_messages import message_bus


class DBusConnection(Channel):
    """A 'plain' D-Bus connection with no matching of replies.

    This doesn't run any separate tasks: sending and receiving are done in
    the task that calls those methods. It's suitable for easily implementing
    servers: several worker tasks can receive requests and send replies.
    For a typical client pattern, see ClientDBusConnection.

    Implements trio's channel interface for Message objects.
    """
    def __init__(self, socket: SocketStream):
        self.socket = socket
        self.parser = Parser()
        self.outgoing_serial = 0
        self.unique_name = None

    async def send(self, message):
        self.outgoing_serial += 1
        message.header.serial = self.outgoing_serial
        await self.socket.send_all(message.serialise())

    async def receive(self):
        while True:
            msg = self.parser.get_next_message()
            if msg is not None:
                return msg

            b = await self.socket.receive_some()
            if not b:
                raise EndOfChannel("Socket closed at the other end")
            self.parser.add_data(b)

    async def aclose(self):
        await self.socket.aclose()


class ClientDBusConnection:
    """A 'client' D-Bus connection which can wait for a specific reply.

    This runs a background receiver task, and makes it possible to send a
    request and wait for the relevant reply. You can also receive the next
    message which someone else isn't waiting for.
    If no-one is waiting for any messages, the receiver task stops reading.
    But if any task is waiting for a reply, messages with no task to receive
    them may be discarded, to avoid them piling up in memory.
    """
    def __init__(self, conn: DBusConnection, nursery: Nursery):
        self._conn = conn
        self.awaiting_reply = {}
        self.awaiting_unmatched = OrderedDict()
        self._unmatched_key = 0
        self._wake_receiver = Event()
        self._rcv_cancel_scope = CancelScope()
        nursery.start_soon(self._receiver)

    async def send(self, message):
        await self._conn.send(message)

    async def send_and_get_reply(self, message):
        serial = self._conn.outgoing_serial + 1
        snd, rcv = open_memory_channel(0)
        self.awaiting_reply[serial] = snd

        try:
            await self.send(message)
            self._wake_receiver.set()
            outc = await rcv.receive()
        finally:
            self.awaiting_reply.pop(serial, None)

        # The outcome here is an exception only if something prevented us
        # from getting a reply. A reply with an error is not turned into an
        # exception at this level.
        return outc.unwrap()

    async def receive_unmatched(self):
        snd, rcv = open_memory_channel(0)
        key = self._unmatched_key
        self._unmatched_key += 1
        self.awaiting_unmatched[key] = snd
        try:
            self._wake_receiver.set()
            outc = await rcv.receive()
        finally:
            self.awaiting_unmatched.pop(key, None)

        return outc.unwrap()

    async def aclose(self):
        self._rcv_cancel_scope.cancel()
        await self._conn.aclose()

    async def _receiver(self):
        try:
            with self._rcv_cancel_scope:
                while True:
                    await self._wake_receiver.wait()

                    if not (self.awaiting_reply or self.awaiting_unmatched):
                        # No-one waiting for a message. Sleep.
                        self._wake_receiver = Event()
                        continue

                    msg = await self._conn.receive()
                    rep_serial = msg.header.fields.get(HeaderFields.reply_serial, -1)
                    chn = self.awaiting_reply.pop(rep_serial, None)
                    if chn is None:
                        if self.awaiting_unmatched:
                            chn = self.awaiting_unmatched.popitem(last=False)
                        else:
                            # Unwanted message, but we still have a reply to find.
                            continue

                    # Hand off the message to the appropriate task
                    try:
                        await chn.send(Value(msg))
                    except Cancelled:
                        await chn.aclose()
                        raise
                    await chn.aclose()

        except trio.EndOfChannel:
            exc = trio.EndOfChannel("D-Bus connection closed from the other side")
        except Exception as e:
            exc = trio.BrokenResourceError("Error receiving D-Bus messages")
            exc.__cause__ = e
            await self.aclose()
        else:
            # The only way out of the loop without an exception reaching here
            # is if the cancel scope was cancelled, which happens if the
            # ClientDBusConnection is closed.
            exc = trio.ClosedResourceError("D-Bus connection closed from this side")

        # Send errors to any tasks still waiting for a message.
        for d in (self.awaiting_reply, self.awaiting_unmatched):
            for chn in d.values():
                try:
                    chn.send_nowait(Error(exc))
                    await chn.aclose()
                except Exception:
                    pass
            d.clear()


class Proxy(ProxyBase):
    def __init__(self, msggen, connection):
        super().__init__(msggen)
        if not isinstance(connection, ClientDBusConnection):
            raise TypeError("Proxy can only be used with RoutingDBusConnection")
        self._connection = connection

    def _method_call(self, make_msg):
        async def inner(*args, **kwargs):
            msg = make_msg(*args, **kwargs)
            assert msg.header.message_type is MessageType.method_call
            return await self._connection.send_and_get_reply(msg)

        return inner


async def connect_and_authenticate(bus='SESSION'):
    """Open a 'plain' D-Bus connection, with no new tasks"""
    bus_addr = get_bus(bus)
    sock : SocketStream = await open_unix_socket(bus_addr)

    # Authentication flow
    await sock.send_all(b'\0' + make_auth_external())
    auth_parser = SASLParser()
    while not auth_parser.authenticated:
        b = await sock.receive_some()
        auth_parser.feed(b)
        if auth_parser.error:
            raise AuthenticationError(auth_parser.error)

    await sock.send_all(BEGIN)
    # Authentication finished

    conn = DBusConnection(sock)

    await conn.send(message_bus.Hello())

    async for in_msg in conn:
        if in_msg.header.fields.get(HeaderFields.reply_serial, -1) == 1:
            conn.unique_name = in_msg.body[0]
            break

    return conn

class _ClientConnectionContext:
    def __init__(self, bus='SESSION'):
        self.bus = bus
        self.nursery_mgr = open_nursery()
        self.client_conn = None

    async def __aenter__(self):
        plain_conn = await connect_and_authenticate(self.bus)
        nursery = await self.nursery_mgr.__aenter__()
        self.client_conn = ClientDBusConnection(plain_conn, nursery)
        return self.client_conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client_conn.aclose()
        await self.nursery_mgr.__aexit__(exc_type, exc_val, exc_tb)

def open_client_connection(bus='SESSION'):
    """Open a 'client' D-Bus connection with a receiver task.

    Use as an async context manager::

        async with open_client_connection() as conn:
            ...
    """
    return _ClientConnectionContext(bus)
