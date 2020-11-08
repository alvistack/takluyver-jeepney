Connecting to DBus and sending messages
=======================================

Jeepney can be used with several different frameworks:

- Blocking I/O
- Multi-threading with the `threading <https://docs.python.org/3/library/threading.html>`_ module
- `Trio <https://trio.readthedocs.io/en/stable/>`_
- `asyncio <https://docs.python.org/3/library/asyncio.html>`_
- `Tornado <http://www.tornadoweb.org/en/stable/>`_

For each of these, there is a module in ``jeepney.io`` providing the
integration layer.

Here's an example of sending a desktop notification, using blocking I/O:

.. literalinclude:: /../examples/blocking_notify.py

And here is the same thing using asyncio:

.. literalinclude:: /../examples/aio_notify_noproxy.py

See the `examples folder <https://gitlab.com/takluyver/jeepney/-/tree/master/examples>`_
in Jeepney's source repository for more examples.

.. _connections_and_routers:

Connections and Routers
-----------------------

Each integration (except blocking I/O) can create *connections* and *routers*.

**Routers** are useful for calling methods in other processes.
Routers let you send a request and wait for a reply, using a
:ref:`proxy <msggen_proxies>` or with ``router.send_and_get_reply()``.
You can also filter incoming messages into queues, e.g. to wait for a specific
signal. But if messages arrive faster than they are processed, these queues fill
up, and messages may be dropped.

**Connections** are simpler: they let you send and receive messages, but
``conn.receive()`` will give you the next message read, whatever that is.
You'd use this to write a server which responds to incoming messages.
A connection will never discard an incoming message.

.. note::

   For blocking, single-threaded I/O, the connection doubles as a router.
   Incoming messages while you're waiting for a reply will be filtered,
   and you can also filter the next message by calling ``conn.recv_messages()``.

   Routers for the other integrations receive messages in a background task.

.. _msggen_proxies:

Message generators and proxies
------------------------------

If you're calling a number of different methods, you can make a *message
generator* class containing their definitions. Jeepney includes a tool to
generate these classes automatically—see :doc:`bindgen`.

Message generators define how to construct messages. *Proxies* are wrappers
around message generators which send a message and get the reply back.

Let's rewrite the example above to use a message generator and a proxy:

.. literalinclude:: /../examples/aio_notify.py

This is more code for the simple use case here, but in a larger application
collecting the message definitions together like this could make it clearer.
