from binascii import hexlify
import os

def make_auth_external():
    hex_uid = hexlify(str(os.getuid()).encode('ascii'))
    return b'AUTH EXTERNAL %b\r\n' % hex_uid

def make_auth_anonymous():
    r"""Format an AUTH command line for the ANONYMOUS mechanism

    The value of "initial-response" (the last arg) is some arbitrary but
    readable string referred to as "message trace" in the RFC:
    <https://tools.ietf.org/html/rfc4505#section-2>.

    An example of how this mechanism might be used as a fallback::

        class SASLParserAnonAuth(SASLParser):
            def __init__(self):
                super().__init__()
                self.rejected = None

            def process_line(self, line):
                self.rejected = None
                if line.startswith(b"REJECTED"):
                    self.rejected = line
                else:
                    super().process_line(line)

            def feed(self, data):
                self.buffer += data
                while ((b'\r\n' in self.buffer)
                       and not self.authenticated
                       and self.rejected is None):
                    line, self.buffer = self.buffer.split(b'\r\n', 1)
                    self.process_line(line)

        class DBusProtocolAnonAuth(DBusProtocol):
            def __init__(self):
                from jeepney.auth import SASLParserAnonAuth
                super().__init__()
                self.auth_parser = SASLParserAnonAuth()

            def data_received(self, data):
                self.auth_parser.feed(data)
                if self.auth_parser.authenticated:
                    self._authenticated()
                    return
                if (not self.auth_parser.error and
                        self.auth_parser.rejected is not None):
                    if b"ANONYMOUS" in self.auth_parser.rejected:
                        from jeepney.auth import make_auth_anonymous
                        self.transport.write(make_auth_anonymous())
                        self.auth_parser.rejected = None
                    else:
                        self.auth_parser.error = self.auth_parser.rejected
                if self.auth_parser.error:
                    self.authentication.set_exception(
                        AuthenticationError(self.auth_parser.error))
    """
    tag = bytes(b'libdbus 1.x.x'.hex(), "UTF-8")  # dbus_get_version
    return b'AUTH ANONYMOUS %s\r\n' % tag

BEGIN = b'BEGIN\r\n'

class SASLParser:
    def __init__(self):
        self.buffer = b''
        self.authenticated = False
        self.error = None

    def process_line(self, line):
        if line.startswith(b'OK '):
            self.authenticated = True
        else:
            self.error = line

    def feed(self, data):
        self.buffer += data
        while (b'\r\n' in data) and not self.authenticated:
            line, self.buffer = self.buffer.split(b'\r\n', 1)
            self.process_line(line)
