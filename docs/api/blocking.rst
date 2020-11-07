Blocking I/O
============

.. module:: jeepney.io.blocking

.. autofunction:: open_dbus_connection

.. autoclass:: DBusConnection

   .. automethod:: send

   .. automethod:: receive

   .. automethod:: send_and_get_reply

   .. automethod:: recv_messages

   .. automethod:: filter

   .. automethod:: close

      Using ``with open_dbus_connection()`` will also close the connection on
      exiting the block.

.. autoclass:: Proxy
