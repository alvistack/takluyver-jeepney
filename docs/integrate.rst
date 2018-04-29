Connecting to DBus and sending messages
=======================================

So far, Jeepney can be used with three different I/O systems:

- Blocking (synchronous) I/O
- `asyncio <https://docs.python.org/3/library/asyncio.html>`_
- `Tornado <http://www.tornadoweb.org/en/stable/>`_

For each of these, there is a module in ``jeepney.integrate`` which exposes
a function called ``connect_and_authenticate``. This establishes a DBus
connection and returns an object you can use to send and receive messages.
Exactly what it returns may vary, though.

Here's an example of sending a desktop notification, using blocking I/O:

.. literalinclude:: /../examples/blocking_notify.py

And here is the same thing using asyncio:

.. literalinclude:: /../examples/aio_notify_noproxy.py

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
