Generating D-Bus wrappers
=========================

D-Bus includes a mechanism to introspect remote objects and discover the methods
they define. Jeepney can use this to generate classes defining the messages to
send. Use it like this::

    python3 -m jeepney.bindgen --name org.freedesktop.Notifications \
            --path /org/freedesktop/Notifications

This command will produce the code used in the previous page (see
:ref:`msggen_proxies`).

You specify *name*—which D-Bus service you're talking to—and *path*—an
object in that service. Jeepney will generate a wrapper for each interface that
object has, except for some standard ones like the introspection interface
itself.
