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

    For an example showing this mechanism used as a fallback, see:
    <FIXME>
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
