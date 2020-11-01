"""Synchronous IO wrappers around jeepney
"""
from collections import deque
from errno import ECONNRESET
import functools
from itertools import count
import os
from selectors import DefaultSelector, EVENT_READ
import socket
import time

from jeepney import Parser, Message, MessageType, HeaderFields
from jeepney.auth import SASLParser, make_auth_external, BEGIN, AuthenticationError
from jeepney.bus import get_bus
from jeepney.wrappers import ProxyBase, unwrap_msg
from jeepney.routing import Router
from jeepney.bus_messages import message_bus


class _Future:
    def __init__(self):
        self._result = None

    def done(self):
        return bool(self._result)

    def set_exception(self, exception):
        self._result = (False, exception)

    def set_result(self, result): 
        self._result = (True, result)

    def result(self):
        success, value = self._result
        if success:
            return value
        raise value


class DBusConnection:
    def __init__(self, sock):
        self.sock = sock
        self.parser = Parser()
        self.outgoing_serial = count(start=1)
        self.selector = DefaultSelector()
        self.select_key = self.selector.register(sock, EVENT_READ)

        # Message routing machinery
        self.router = Router(_Future)
        self._filters = {}
        self._filter_ids = count()

        # Say Hello, get our unique name
        self.bus_proxy = Proxy(message_bus, self)
        hello_reply = self.bus_proxy.Hello()
        self.unique_name = hello_reply[0]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def send(self, message: Message, serial=None):
        """Serialise and send a :class:`~.Message` object"""
        if serial is None:
            serial = next(self.outgoing_serial)
        data = message.serialise(serial=serial)
        self.sock.sendall(data)

    send_message = send  # Backwards compatibility

    def receive(self, timeout=None) -> Message:
        """Return the next available message from the connection

        If the data is ready, this will return immediately, even if timeout<=0.
        Otherwise, it will wait for up to timeout seconds, or indefinitely if
        timeout is None. If no message comes in time, it raises TimeoutError.
        """
        if timeout is not None:
            deadline = time.monotonic() + timeout
        else:
            deadline = None

        while True:
            msg = self.parser.get_next_message()
            if msg is not None:
                return msg

            if deadline is not None:
                timeout = deadline - time.monotonic()

            b = self._read_some_data(timeout)
            self.parser.add_data(b)

    def _read_some_data(self, timeout=None):
        for key, ev in self.selector.select(timeout):
            if key == self.select_key:
                return unwrap_read(self.sock.recv(4096))

        raise TimeoutError

    def recv_messages(self, timeout=None):
        """Receive one message and apply filters

        See :meth:`add_filter`. Returns nothing.
        """
        msg = self.receive(timeout=timeout)
        self.router.incoming(msg)
        for rule, chan in self._filters.values():
            if rule.matches(msg):
                chan.append(msg)

    def send_and_get_reply(self, message, timeout=None, unwrap=True):
        """Send a message, wait for the reply and return it

        Filters are applied to other messages received before the reply -
        see :meth:`add_filter`.
        """
        if timeout is not None:
            deadline = time.monotonic() + timeout
        else:
            deadline = None

        serial = next(self.outgoing_serial)
        self.send_message(message, serial=serial)
        while True:
            if deadline is not None:
                timeout = deadline - time.monotonic()
            msg_in = self.receive(timeout=timeout)
            reply_to = msg_in.header.fields.get(HeaderFields.reply_serial, -1)
            if reply_to == serial:
                if unwrap:
                    return unwrap_msg(msg_in)
                return msg_in

            # Not the reply
            self.router.incoming(msg_in)
            for rule, chan in self._filters.values():
                if rule.matches(msg_in):
                    chan.append(msg_in)

    def add_filter(self, rule, channel: deque):
        """Create a filter for incoming messages

        :param jeepney.MatchRule rule: Catch messages matching this rule
        :param collections.deque channel: Matched messages will be added to this
        :return: A filter ID to use with :meth:`remove_filter`
        """
        fid = next(self._filter_ids)
        self._filters[fid] = (rule, channel)
        return fid

    def remove_filter(self, filter_id) -> deque:
        """Remove a previously added filter"""
        return self._filters.pop(filter_id)[1]

    def close(self):
        """Close this connection"""
        self.selector.close()
        self.sock.close()

class Proxy(ProxyBase):
    """A blocking proxy for calling D-Bus methods

    :param msggen: A message generator object.
    :param ~blocking.DBusConnection connection: Connection to send and receive messages.
    :param float timeout: Seconds to wait for a reply, or None for no limit.
    """
    def __init__(self, msggen, connection, timeout=None):
        super().__init__(msggen)
        self._connection = connection
        self._timeout = timeout

    def __repr__(self):
        extra = '' if (self._timeout is None) else f', timeout={self._timeout}'
        return f"Proxy({self._msggen}, {self._connection}{extra})"

    def _method_call(self, make_msg):
        @functools.wraps(make_msg)
        def inner(*args, **kwargs):
            msg = make_msg(*args, **kwargs)
            assert msg.header.message_type is MessageType.method_call
            return self._connection.send_and_get_reply(msg, timeout=self._timeout)

        return inner


def unwrap_read(b):
    """Raise ConnectionResetError from an empty read.

    Sometimes the socket raises an error itself, sometimes it gives no data.
    I haven't worked out when it behaves each way.
    """
    if not b:
        raise ConnectionResetError(ECONNRESET, os.strerror(ECONNRESET))
    return b


def connect_and_authenticate(bus='SESSION') -> DBusConnection:
    """Connect to a D-Bus message bus"""
    bus_addr = get_bus(bus)
    sock = socket.socket(family=socket.AF_UNIX)
    sock.connect(bus_addr)
    sock.sendall(b'\0' + make_auth_external())
    auth_parser = SASLParser()
    while not auth_parser.authenticated:
        auth_parser.feed(unwrap_read(sock.recv(1024)))
        if auth_parser.error:
            raise AuthenticationError(auth_parser.error)

    sock.sendall(BEGIN)

    conn = DBusConnection(sock)
    conn.parser.buf = auth_parser.buffer
    return conn

open_dbus_connection = connect_and_authenticate

if __name__ == '__main__':
    conn = connect_and_authenticate()
    print("Unique name:", conn.unique_name)
