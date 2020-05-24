Authentication
==============

If you are setting up a socket for D-Bus, you will need to do `SASL
<https://en.wikipedia.org/wiki/Simple_Authentication_and_Security_Layer>`_
authentication before starting to send and receive D-Bus messages.
This text based protocol is completely different to standard D-Bus.

.. note::

   If you use any of Jeepney's I/O integration layers, authentication is built
   in. You only need these functions if you're working outside that.

.. module:: jeepney.auth

.. autofunction:: make_auth_external

.. autofunction:: make_auth_anonymous

.. data:: BEGIN
   :type: bytes

   Send this just before switching to the D-Bus protocol.

.. autoclass:: SASLParser

   .. attribute:: authenticated
      :type: bool

      Initially False, changes to True when authentication has succeeded.

   .. attribute:: error

      ``None``, or the raw bytes of an error message if authentication failed.

   .. automethod:: feed

.. autoexception:: AuthenticationError

Typical flow
------------

- Send a null byte to start.
- Prepare & send an AUTH command, e.g. from :func:`make_auth_external`.
- Feed received data to :class:`SASLParser` until either
  :attr:`~.SASLParser.authenticated` or :attr:`~.SASLParser.error` is set.
- Send :data:`BEGIN`.
- Start sending & receiving D-Bus messages.
