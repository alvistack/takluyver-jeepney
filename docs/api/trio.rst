Trio integration
================

.. module:: jeepney.io.trio

.. autofunction:: open_dbus_router

.. autoclass:: DBusRouter

   .. automethod:: send

   .. automethod:: send_and_get_reply

   .. automethod:: filter

   .. automethod:: aclose

      Leaving the ``async with`` block will also close the router.

.. autoclass:: Proxy

.. autofunction:: open_dbus_connection

.. autoclass:: DBusConnection

   .. automethod:: send

   .. automethod:: receive

   .. automethod:: router

   .. automethod:: aclose
