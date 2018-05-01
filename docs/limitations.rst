Limitations
===========

Some lesser-used parts of the D-Bus spec are not implemented:

1. Jeepney only connects to Unix domain sockets.
   This is how D-Bus is normally exposed,
   but the specification allows for other transports, such as TCP sockets,
   which Jeepney does not support.
2. Only the 'external' auth method is used.
   The specification recommends this mechanism where it's available,
   and it's the obvious thing to use with Unix domain sockets.
3. Sending and receiving Unix file descriptors is not supported.

Any of these limitations may be lifted in the future,
if there's a need and we can find a clean way to do so.
If you want to remove a limitation, be prepared to get involved. :-)
