Release notes
=============

0.5
---

* New common scheme for I/O integration - see :ref:`connections_and_routers`.

  * This is designed for tasks to wait for messages and then act on them,
    rather than triggering callbacks. This is based on ideas from 'structured
    concurrency', which also informs the design of Trio. See `this blog post
    by Nathaniel Smith <https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/>`_
    for more background.
  * There are new integrations for :doc:`Trio <api/trio>` and :doc:`threading
    <api/threading>`.
  * The old integration interfaces should still work for now, but they will be
    deprecated and eventually removed.

* :meth:`.Message.serialise` accepts a serial number, to serialise outgoing
  messages without modifying the message object.
* Improved documentation, including :doc:`API docs <api/index>`.

0.4.3
-----

* The blocking integration now throws ``ConnectionResetError`` on all systems
  when the connection was closed from the other end. It would previously hang
  on some systems.

0.4.2
-----

* The blocking ``DBusConnection`` integration class now has a ``.close()``
  method, and can be used as a context manager::

    from jeepney.integrate.blocking import connect_and_authenticate
    with connect_and_authenticate() as connection:
        ...

0.4.1
-----

* Avoid using :class:`asyncio.Future` for the blocking integration.
* Set the 'destination' field on method return and error messages to the
  'sender' from the parent message.

Thanks to Oscar Caballero and Thomas Grainger for contributing to this release.

0.4
---

* Authentication failures now raise a new :exc:`AuthenticationError`
  subclass of :exc:`ValueError`, so that they can be caught specifically.
* Fixed logic error when authentication is rejected.
* Use *effective* user ID for authentication instead of *real* user ID.
  In typical use cases these are the same, but where they differ, effective
  uid seems to be the relevant one.
* The 64 MiB size limit for an array is now checked when serialising it.
* New function :func:`jeepney.auth.make_auth_anonymous` to prepare an anonymous
  authentication message. This is not used by the wrappers in Jeepney at the
  moment, but may be useful for third party code in some situations.
* New examples for subscribing to D-Bus signals, with blocking I/O and with
  asyncio.
* Various improvements to documentation.

Thanks to Jane Soko and Gitlab user xiretza for contributing to this release.
