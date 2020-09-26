Trio integration
================

.. module:: jeepney.integrate.trio

.. autofunction:: open_dbus_router

.. autoclass:: DBusRouter

   .. automethod:: send

   .. automethod:: send_and_get_reply

   .. automethod:: add_filter

   .. automethod:: remove_filter

   .. automethod:: aclose

      Leaving the ``async with`` block will also close the router.

.. autoclass:: Proxy

.. autofunction:: open_dbus_connection

.. autoclass:: DBusConnection

   .. automethod:: send

   .. automethod:: receive

   .. automethod:: router

   .. automethod:: aclose
