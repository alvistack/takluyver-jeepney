import asyncio

from jeepney.auth import SASLParser, make_auth_external, BEGIN
from jeepney.bus import get_bus
from jeepney.low_level import Parser, HeaderFields, MessageType
from jeepney.wrappers import hello_msg

class DBusProtocol(asyncio.Protocol):
    def __init__(self):
        self.auth_parser = SASLParser()
        self.parser = Parser()
        self.outgoing_serial = 0
        self.awaiting_reply = {}
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
            self.authentication.set_exception(ValueError(self.auth_parser.error))

    def data_received_post_auth(self, data):
        for msg in self.parser.feed(data):
            reply_serial = msg.header.fields.get(HeaderFields.reply_serial, -1)
            if reply_serial in self.awaiting_reply:
                self.awaiting_reply[reply_serial].set_result(msg)

    def send_message(self, message):
        if not self.authentication.done():
            raise RuntimeError("Wait for authentication before sending messages")

        fut = None
        if message.header.serial == -1:
            self.outgoing_serial += 1
            message.header.serial = self.outgoing_serial
        if message.header.message_type == MessageType.method_call:
            fut = asyncio.Future()
            self.awaiting_reply[message.header.serial] = fut
        data = message.serialise()
        self.transport.write(data)
        return fut

async def connect_and_authenticate(bus='SESSION', loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    (t, p) = await loop.create_unix_connection(DBusProtocol, path=get_bus(bus))
    await p.authentication
    hello_reply = await p.send_message(hello_msg())
    p.unique_name = hello_reply.body[0]
    return (t, p)
