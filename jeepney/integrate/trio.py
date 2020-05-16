import logging
from outcome import Value, Error
import trio
from trio import (
    open_unix_socket, open_nursery,
    Cancelled, CancelScope, SocketStream, EndOfChannel, Nursery
)
from trio.abc import Channel, SendChannel
from trio.hazmat import Abort, current_task, reschedule, wait_task_rescheduled

from jeepney.auth import SASLParser, make_auth_external, BEGIN, AuthenticationError
from jeepney.bus import get_bus
from jeepney.low_level import Parser, MessageType, Message, HeaderFields
from jeepney.wrappers import ProxyBase
from jeepney.bus_messages import message_bus

log = logging.getLogger(__name__)


class DBusConnection(Channel):
    """A 'plain' D-Bus connection with no matching of replies.

    This doesn't run any separate tasks: sending and receiving are done in
    the task that calls those methods. It's suitable for easily implementing
    servers: several worker tasks can receive requests and send replies.
    For a typical client pattern, see DBusRequester.

    Implements trio's channel interface for Message objects.
    """
    def __init__(self, socket: SocketStream):
        self.socket = socket
        self.parser = Parser()
        self.outgoing_serial = 0
        self.unique_name = None
        self.send_lock = trio.Lock()

    async def send(self, message: Message):
        self.outgoing_serial += 1
        message.header.serial = self.outgoing_serial
        async with self.send_lock:
            await self.socket.send_all(message.serialise())

    async def receive(self) -> Message:
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

    def requester(self):
        """Temporarily wrap this connection as a DBusRequester

        To be used like::

            async with conn.requester() as req:
                reply = await req.send_and_get_reply(msg)

        While the requester is running, you shouldn't use :meth:`receive`.
        Once the requester is closed, you can use the plain connection again.
        """
        return DBusRequester(self)


async def connect_and_authenticate(bus='SESSION') -> DBusConnection:
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

    # Say *Hello* to the message bus - this must be the first message, and the
    # reply gives us our unique name.
    async with conn.requester() as requester:
        reply = await requester.send_and_get_reply(message_bus.Hello())
        conn.unique_name = reply.body[0]

    return conn


class DummySendChannel(SendChannel):
    """A send channel that accepts & discards messages"""
    async def send(self, value):
        pass

    async def send_nowait(self, value):
        pass

    async def aclose(self):
        pass


class Future:
    """A Future for trio.

    Is this a bad idea? Trio doesn't offer futures itself, but I couldn't find
    a neater way to achieve what I wanted.
    """
    def __init__(self):
        self._outcome = None
        self._task = None

    def set(self, outcome):
        self._outcome = outcome
        if self._task is not None:
            reschedule(self._task, outcome)

    async def get(self):
        if self._outcome is not None:
            await trio.hazmat.checkpoint()
            return self._outcome.unwrap()

        self._task = current_task()

        def abort_fn(_):
            self._task = None
            return Abort.SUCCEEDED

        return (await wait_task_rescheduled(abort_fn))


class DBusRequester:
    """A 'client' D-Bus connection which can wait for a specific reply.

    This runs a background receiver task, and makes it possible to send a
    request and wait for the relevant reply.
    """
    _nursery_mgr = None
    _rcv_cancel_scope = None
    is_running = False

    def __init__(self, conn: DBusConnection,
                 incoming_method_calls=None):
        self._conn = conn
        self._reply_futures = {}
        self._incoming_calls = incoming_method_calls or DummySendChannel()

    async def send(self, message):
        await self._conn.send(message)

    async def send_and_get_reply(self, message) -> Message:
        """Send a method call message and wait for the reply

        Returns the reply message (method return or error message type).
        """
        if message.header.message_type != MessageType.method_call:
            raise TypeError("Only method call messages have replies")
        if not self.is_running:
            raise RuntimeError("Receiver task is not running")
        serial = self._conn.outgoing_serial + 1
        self._reply_futures[serial] = reply_fut = Future()

        try:
            await self.send(message)
            return (await reply_fut.get())
        finally:
            del self._reply_futures[serial]

    # Task management -------------------------------------------

    async def start(self, nursery: Nursery):
        if self.is_running:
            raise RuntimeError("Receiver is already running")
        self._rcv_cancel_scope = await nursery.start(self._receiver)

    async def aclose(self):
        """Stop the receiver loop"""
        if self._rcv_cancel_scope is not None:
            self._rcv_cancel_scope.cancel()
            self._rcv_cancel_scope = None

    async def __aenter__(self):
        self._nursery_mgr = trio.open_nursery()
        nursery = await self._nursery_mgr.__aenter__()
        await self.start(nursery)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
        await self._nursery_mgr.__aexit__(exc_type, exc_val, exc_tb)
        self._nursery_mgr = None

    # Code to run in receiver task ------------------------------------

    def _dispatch(self, msg):
        """Handle one received message"""
        msg_type = msg.header.message_type
        if msg_type == MessageType.method_call:
            try:
                self._incoming_calls.send_nowait(msg)
            except trio.WouldBlock:
                log.debug("Discarded incoming method call (queue full): %s", msg)

        elif msg_type in (MessageType.method_return, MessageType.error):
            rep_serial = msg.header.fields.get(HeaderFields.reply_serial, -1)
            fut = self._reply_futures.get(rep_serial, None)
            if fut is not None:
                fut.set(Value(msg))
            else:
                log.debug("Discarded reply (nothing waiting for it): %s", msg)

        else:
            log.debug("Discarded signal message: %s", msg)

    async def _receiver(self, task_status=trio.TASK_STATUS_IGNORED):
        """Receiver loop - runs in a separate task"""
        with CancelScope() as cscope:
            self.is_running = True
            task_status.started(cscope)
            try:
                while True:
                    msg = await self._conn.receive()
                    self._dispatch(msg)
            finally:
                self.is_running = False
                # Send errors to any tasks still waiting for a message.
                futures, self._reply_futures = self._reply_futures, {}
                for fut in futures.values():
                    fut.set(Error(NoReplyError("Reply receiver stopped")))

                await self._incoming_calls.aclose()


class NoReplyError(Exception):
    pass


class Proxy(ProxyBase):
    def __init__(self, msggen, requester):
        super().__init__(msggen)
        if not isinstance(requester, DBusRequester):
            raise TypeError("Proxy can only be used with DBusRequester")
        self._requester = requester

    def _method_call(self, make_msg):
        async def inner(*args, **kwargs):
            msg = make_msg(*args, **kwargs)
            assert msg.header.message_type is MessageType.method_call
            return await self._requester.send_and_get_reply(msg)

        return inner


class _ClientConnectionContext:
    conn = None
    req_ctx = None

    def __init__(self, bus='SESSION'):
        self.bus = bus

    async def __aenter__(self):
        self.conn = await connect_and_authenticate(self.bus)
        self.req_ctx = self.conn.requester()
        return await self.req_ctx.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.req_ctx.__aexit__(exc_type, exc_val, exc_tb)
        await self.conn.aclose()


def open_requester(bus='SESSION'):
    """Open a 'client' D-Bus connection with a receiver task.

    Use as an async context manager::

        async with open_requester() as req:
            ...

    This is a shortcut for::

        conn = await connect_and_authenticate()
        async with conn:
            async with conn.requester() as req:
                ...
    """
    return _ClientConnectionContext(bus)
