import array
import os
import socket
from warnings import warn

class WrappedFD:
    """A file descriptor received in a D-Bus message

    This wrapper helps ensure that the file descriptor is closed exactly once.
    You can convert it into a file or socket object.
    """
    __slots__ = ('_fd',)
    _CLOSED = -1
    _CONVERTED = -2

    def __init__(self, fd):
        self._fd = fd

    def __repr__(self):
        detail = self._fd
        if self._fd == self._CLOSED:
            detail = 'closed'
        elif self._fd == self._CONVERTED:
            detail = 'converted'
        return f"<WrappedFD ({detail})>"

    def close(self):
        """Close the file descriptor

        This can safely be called multiple times, but will raise RuntimeError
        if called after converting it with one of the ``to_*`` methods.

        This object can also be used in a ``with`` block, and then leaving the
        block closes it.
        """
        if self._fd == self._CLOSED:
            pass
        elif self._fd == self._CONVERTED:
            raise RuntimeError("Can't close WrappedFD after converting it")
        else:
            self._fd, fd = self._CLOSED, self._fd
            os.close(fd)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        if self._fd >= 0:
            warn(
                f'WrappedFD ({self._fd}) was neither closed nor converted',
                ResourceWarning, stacklevel=2, source=self
            )
            self.close()

    def fileno(self):
        """Get the integer file descriptor, without affecting the wrapper"""
        return self._fd

    def to_raw_fd(self):
        """Convert to the low-level integer file descriptor

        The wrapper object can't be used after calling this. The caller is
        responsible for closing the file descriptor.
        """
        self._fd, fd = self._CONVERTED, self._fd
        return fd

    def to_file(self, mode, buffering=-1, encoding=None, errors=None, newline=None):
        """Convert to a Python file object

        The arguments are the same as for the builtin :func:`open` function.

        The wrapper object can't be used after calling this. Closing the file
        object will also close the file descriptor.
        """
        f = open(
            self._fd, mode, buffering=buffering,
            encoding=encoding, errors=errors, newline=newline
        )
        self._fd = self._CONVERTED
        return f

    def to_socket(self):
        """Convert to a socket object

        This returns a standard library :class:`socket.socket` object.

        The wrapper object can't be used after calling this. Closing the socket
        object will also close the file descriptor.
        """
        from socket import socket
        s = socket(fileno=self._fd)
        self._fd = self._CONVERTED
        return s

    @classmethod
    def from_ancdata(cls, ancdata) -> ['WrappedFD']:
        """Make a list of WrappedFD from received file descriptors

        ancdata is a list of ancillary data tuples as returned by socket.recvmsg()
        """
        fds = array.array("i")  # Array of ints
        for cmsg_level, cmsg_type, data in ancdata:
            if cmsg_level == socket.SOL_SOCKET and cmsg_type == socket.SCM_RIGHTS:
                # Append data, ignoring any truncated integers at the end.
                fds.frombytes(data[:len(data) - (len(data) % fds.itemsize)])
        return [cls(i) for i in fds]


_fds_buf_size_cache = None

def fds_buf_size():
    # If there may be file descriptors, we try to read 1 message at a time.
    # The reference implementation of D-Bus defaults to allowing 16 FDs per
    # message, and the Linux kernel currently allows 253 FDs per sendmsg()
    # call. So hopefully allowing 256 FDs per recvmsg() will always suffice.
    global _fds_buf_size_cache
    if _fds_buf_size_cache is None:
        maxfds = 256
        fd_size = array.array('i').itemsize
        _fds_buf_size_cache = socket.CMSG_SPACE(maxfds * fd_size)
    return _fds_buf_size_cache
