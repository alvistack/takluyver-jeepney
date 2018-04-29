Making and parsing messages
===========================

The core of Jeepney is code to build, serialise and deserialise DBus messages.

.. module:: jeepney

.. autoclass:: Message

   .. automethod:: serialise

.. autoclass:: Parser

   .. automethod:: feed

Making messages
---------------

.. autoclass:: DBusAddress

.. autofunction:: new_method_call

.. autofunction:: new_method_return

.. autofunction:: new_error

.. autofunction:: new_signal

.. seealso:: :ref:`msggen_proxies`

Signatures
~~~~~~~~~~

DBus is strongly typed, and every message has a *signature* describing the body
data. These are strings using characters such as ``i`` for a signed 32-bit
integer. See the `DBus specification <https://dbus.freedesktop.org/doc/dbus-specification.html#type-system>`_
for the full list.

Jeepney does not try to guess or discover the signature when you build a
message: your code must explicitly specify a signature for every message.
However, Jeepney can help you write this code: see :doc:`bindgen`.

In most cases, DBus types have an obvious corresponding type in Python. However,
a few types require further explanation:

* DBus *ARRAY* are Python lists, except for arrays of *DICT_ENTRY*, which are
  dicts.
* DBus *STRUCT* are Python tuples.
* DBus *VARIANT* are 2-tuples ``(signature, data)``. E.g. to put a string into
  a variant field, you would pass the data ``("s", "my string")``.
* Jeepney does not (yet) support sending or receiving file descriptors.

