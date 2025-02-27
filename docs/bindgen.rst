Generating D-Bus wrappers
=========================

D-Bus includes a mechanism to introspect remote objects and discover the methods
they define. Jeepney can use this to generate classes defining the messages to
send. Use it like this::

    python3 -m jeepney.bindgen --name org.freedesktop.Notifications \
            --path /org/freedesktop/Notifications

This command will produce the class in the example under :ref:`msggen_proxies`.

You specify *name*—which D-Bus service you're talking to—and *path*—an
object in that service. Jeepney will generate a wrapper for each interface that
object has, except for some standard ones like the introspection interface
itself.

You are welcome to edit the generated code, e.g. to add docstrings or give
parameters meaningful names. Names like ``arg_1`` are created when
introspection doesn't provide a name.


Bindgen command options
-----------------------

.. program:: python -m jeepney.bindgen

.. option:: -n <bus name>, --name <bus name>

   Bus name to introspect, required unless using :option:`--file`.

.. option:: -p <object path>, --path <object path>

   Object path to introspect, required unless using :option:`--file`.
   Bindings will be generated for all interfaces this object exposes, except
   for common interfaces like 'Introspectable'.

.. option:: --bus <bus>

   Bus to connect to, SESSION (default) or SYSTEM.

.. option:: -f <path>, --file <path>

   An XML file to use as input instead of connecting to D-Bus and using
   introspection. The options above are ignored if this is used.

.. option:: -o <path>, --output <path>

   Write the output (Python code) to the specified file.
   By default, a filename is chosen based on the input.
