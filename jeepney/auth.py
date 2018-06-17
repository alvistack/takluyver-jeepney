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
    """
    if make_auth_anonymous.ALLOW is False:
        raise RuntimeError("The ANONYMOUS authentication mechanism is not "
                           "supported by default. See source for details.")
    tag = bytes(b'libdbus 1.x.x'.hex(), "UTF-8")  # dbus_get_version
    return b'AUTH ANONYMOUS %s\r\n' % tag

make_auth_anonymous.ALLOW = False

BEGIN = b'BEGIN\r\n'


class SASLParser:
    def __init__(self):
        self.buffer = b''
        self.authenticated = False
        self.rejected = None
        self.error = None

    def process_line(self, line):
        self.rejected = None
        if make_auth_anonymous.ALLOW and line.startswith(b"REJECTED"):
            self.rejected = line
        elif line.startswith(b'OK '):
            self.authenticated = True
        else:
            self.error = line

    def feed(self, data):
        self.buffer += data
        while ((b'\r\n' in data) and not self.authenticated
               and self.rejected is None):
            line, self.buffer = self.buffer.split(b'\r\n', 1)
            self.process_line(line)
