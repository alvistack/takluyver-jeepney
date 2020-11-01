import asyncio
from itertools import count

from jeepney.auth import SASLParser, make_auth_external, BEGIN, AuthenticationError
from jeepney.bus import get_bus
from jeepney import HeaderFields, Message, MessageType, Parser
from jeepney.wrappers import ProxyBase, unwrap_msg
from jeepney.routing import Router
from jeepney.bus_messages import message_bus


class DBusConnection:
    """A plain D-Bus connection with no matching of replies.

    This doesn't run any separate tasks: sending and receiving are done in
    the task that calls those methods. It's suitable for implementing servers:
    several worker tasks can receive requests and send replies.
    For a typical client pattern, see :class:`DBusRouter`.
    """
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.parser = Parser()
        self.outgoing_serial = count(start=1)
        self.unique_name = None
        self.send_lock = asyncio.Lock()

    async def send(self, message: Message, *, serial=None):
        """Serialise and send a :class:`~.Message` object"""
        async with self.send_lock:
            if serial is None:
                serial = next(self.outgoing_serial)
            self.writer.write(message.serialise(serial))
            await self.writer.drain()

    async def receive(self) -> Message:
        """Return the next available message from the connection"""
        while True:
            msg = self.parser.get_next_message()
            if msg is not None:
                return msg

            b = await self.reader.read(4096)
            if not b:
                raise EOFError
            self.parser.add_data(b)

    async def close(self):
        """Close the D-Bus connection"""
        self.writer.close()
        await self.writer.wait_closed()


async def open_dbus_connection(bus='SESSION'):
    """Open a plain D-Bus connection

    :return: :class:`DBusConnection`
    """
    bus_addr = get_bus(bus)
    reader, writer = await asyncio.open_unix_connection(bus_addr)

    # Authentication flow
    writer.write(b'\0' + make_auth_external())
    await writer.drain()
    auth_parser = SASLParser()
    while not auth_parser.authenticated:
        b = await reader.read(1024)
        if not b:
            raise EOFError("Socket closed before authentication")
        auth_parser.feed(b)
        if auth_parser.error:
            raise AuthenticationError(auth_parser.error)

    writer.write(BEGIN)
    await writer.drain()
    # Authentication finished

    conn = DBusConnection(reader, writer)
    conn.parser.add_data(auth_parser.buffer)

    # Say *Hello* to the message bus - this must be the first message, and the
    # reply gives us our unique name.
    async with DBusRouter(conn) as router:
        reply_body = await asyncio.wait_for(Proxy(message_bus, router).Hello(), 10)
        conn.unique_name = reply_body[0]

    return conn

class DBusRouter:
    """A 'client' D-Bus connection which can wait for a specific reply.

    This runs a background receiver task, and makes it possible to send a
    request and wait for the relevant reply.
    """
    _nursery_mgr = None
    _send_cancel_scope = None
    _rcv_cancel_scope = None
    is_running = False

    def __init__(self, conn: DBusConnection):
        self._conn = conn
        self._reply_futures = {}
        self._filters = {}
        self._filter_ids = count()
        self._rcv_task = asyncio.create_task(self._receiver())

    async def send(self, message, *, serial=None):
        """Send a message, don't wait for a reply"""
        await self._conn.send(message, serial=serial)

    async def send_and_get_reply(self, message) -> Message:
        """Send a method call message and wait for the reply

        Returns the reply message (method return or error message type).
        """
        if message.header.message_type != MessageType.method_call:
            raise TypeError("Only method call messages have replies")
        if self._rcv_task.done():
            raise RuntimeError("Receiver task is not running")

        serial = next(self._conn.outgoing_serial)
        self._reply_futures[serial] = reply_fut = asyncio.Future()

        try:
            await self.send(message, serial=serial)
            return (await reply_fut)
        finally:
            del self._reply_futures[serial]

    def add_filter(self, rule, channel: asyncio.Queue):
        """Create a filter for incoming messages

        :param MatchRule rule: Catch messages matching this rule
        :param asyncio.Queue channel: Send matching messages here
        :return: A filter ID to use with :meth:`remove_filter`
        """
        fid = next(self._filter_ids)
        self._filters[fid] = (rule, channel)
        return fid

    def remove_filter(self, filter_id):
        """Remove a previously added filter"""
        return self._filter_ids.pop(filter_id)[1]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._rcv_task.cancel()
        return False

    # Code to run in receiver task ------------------------------------

    def _dispatch(self, msg: Message):
        """Handle one received message"""
        msg_type = msg.header.message_type

        if msg_type in (MessageType.method_return, MessageType.error):
            rep_serial = msg.header.fields.get(HeaderFields.reply_serial, -1)
            fut = self._reply_futures.get(rep_serial, None)
            if fut is not None:
                fut.set_result(msg)
                return

        for rule, q in self._filters.values():
            if rule.matches(msg):
                try:
                    q.put_nowait(msg)
                except asyncio.QueueFull:
                    pass

    async def _receiver(self):
        """Receiver loop - runs in a separate task"""
        try:
            while True:
                msg = await self._conn.receive()
                self._dispatch(msg)
        finally:
            self.is_running = False
            # Send errors to any tasks still waiting for a message.
            futures, self._reply_futures = self._reply_futures, {}
            for fut in futures.values():
                fut.set_exception(NoReplyError("Reply receiver stopped"))

class open_dbus_router:
    """Open a D-Bus 'router' to send and receive messages

    Use as an async context manager::

        async with open_dbus_router() as router:
            ...
    """
    conn = None
    req_ctx = None

    def __init__(self, bus='SESSION'):
        self.bus = bus

    async def __aenter__(self):
        self.conn = await open_dbus_connection(self.bus)
        self.req_ctx = DBusRouter(self.conn)
        return await self.req_ctx.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.req_ctx.__aexit__(exc_type, exc_val, exc_tb)
        await self.conn.close()


class NoReplyError(Exception):
    pass


class DBusProtocol(asyncio.Protocol):
    def __init__(self):
        self.auth_parser = SASLParser()
        self.parser = Parser()
        self.router = Router(asyncio.Future)
        self.authentication = asyncio.Future()
        self.unique_name = None

    def connection_made(self, transport):
        self.transport = transport
        self.transport.write(b'\0' + make_auth_external())

    def _authenticated(self):
        self.transport.write(BEGIN)
        self.authentication.set_result(True)
        self.data_received = self.data_received_post_auth
        self.data_received(self.auth_parser.buffer)

    def data_received(self, data):
        self.auth_parser.feed(data)
        if self.auth_parser.authenticated:
            self._authenticated()
        elif self.auth_parser.error:
            self.authentication.set_exception(AuthenticationError(self.auth_parser.error))

    def data_received_post_auth(self, data):
        for msg in self.parser.feed(data):
            self.router.incoming(msg)

    def send_message(self, message):
        if not self.authentication.done():
            raise RuntimeError("Wait for authentication before sending messages")

        future = self.router.outgoing(message)
        data = message.serialise()
        self.transport.write(data)
        return future

    async def send_and_get_reply(self, message):
        if message.header.message_type != MessageType.method_call:
            raise TypeError("Only method call messages have replies")

        return await self.send_message(message)

class Proxy(ProxyBase):
    """An asyncio proxy for calling D-Bus methods

    :param msggen: A message generator object.
    :param ~asyncio.DBusRouter router: Router to send and receive messages.
    """
    def __init__(self, msggen, router):
        super().__init__(msggen)
        self._router = router

    def __repr__(self):
        return 'Proxy({}, {})'.format(self._msggen, self._router)

    def _method_call(self, make_msg):
        async def inner(*args, **kwargs):
            msg = make_msg(*args, **kwargs)
            assert msg.header.message_type is MessageType.method_call
            reply = await self._router.send_and_get_reply(msg)

            # New implementation (DBusRouter) gives a Message object back,
            # but the older DBusProtocol unwraps it for us.
            if isinstance(reply, Message):
                reply = unwrap_msg(reply)
            return reply

        return inner


async def connect_and_authenticate(bus='SESSION', loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    (t, p) = await loop.create_unix_connection(DBusProtocol, path=get_bus(bus))
    await p.authentication
    bus = Proxy(message_bus, p)
    hello_reply = await bus.Hello()
    p.unique_name = hello_reply[0]
    return (t, p)
