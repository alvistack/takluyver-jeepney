"""Synchronous IO wrappers around jeepney
"""
import socket

from jeepney.auth import SASLParser, make_auth_external, BEGIN
from jeepney.bus import get_bus
from jeepney.low_level import Parser, HeaderFields, MessageType
from jeepney.wrappers import hello_msg, DBusErrorResponse

class DBusConnection:
    def __init__(self, sock):
        self.sock = sock
        self.parser = Parser()
        self.outgoing_serial = 0
        hello_reply = self.send_and_get_reply(hello_msg())
        self.unique_name = hello_reply.body[0]

    def send_message(self, message):
        if message.header.serial == -1:
            self.outgoing_serial += 1
            message.header.serial = self.outgoing_serial
        data = message.serialise()
        self.sock.sendall(data)

    def recv_messages(self):
        while True:
            b = self.sock.recv(4096)
            msgs = self.parser.feed(b)
            if msgs:
                return msgs

    def send_and_get_reply(self, message):
        """Send a message, wait for the reply and return it.

        This will discard any other incoming messages until it finds the reply.
        """
        self.send_message(message)
        serial = message.header.serial
        while True:
            msgs = self.recv_messages()
            for msg in msgs:
                if serial == msg.header.fields.get(HeaderFields.reply_serial, -1):
                    if msg.header.message_type is MessageType.error:
                        raise DBusErrorResponse(msg.body)
                    return msg


def connect_and_authenticate(bus='SESSION'):
    bus_addr = get_bus(bus)
    sock = socket.socket(family=socket.AF_UNIX)
    sock.connect(bus_addr)
    sock.sendall(b'\0' + make_auth_external())
    auth_parser = SASLParser()
    while not auth_parser.authenticated:
        auth_parser.feed(sock.recv(1024))
        if auth_parser.error:
            raise Exception("Authentication failed: %r" % auth_parser.error)

    sock.sendall(BEGIN)

    conn = DBusConnection(sock)
    conn.parser.buf = auth_parser.buffer
    return conn
