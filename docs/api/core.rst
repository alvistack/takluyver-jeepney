Core API
========

.. module:: jeepney

Message constructors
--------------------

.. autofunction:: new_method_call

.. autofunction:: new_method_return

.. autofunction:: new_error

.. autofunction:: new_signal

.. autoclass:: DBusAddress

.. autoclass:: MessageGenerator

   .. seealso:: :doc:`/bindgen`

Parsing
-------

.. autoclass:: Parser

Message objects
---------------

.. autoclass:: Message

   .. attribute:: header

      A :class:`Header` object

   .. attribute:: body

      A tuple of the data in this message. The number and types of the elements
      depend on the message's signature:

      ===========    ==========  ===========
      D-Bus type     D-Bus code  Python type
      ===========    ==========  ===========
      BYTE            ``y``      int
      BOOLEAN         ``b``      int
      INT16           ``n``      int
      UINT16          ``q``      int
      INT32           ``i``      int
      UINT32          ``u``      int
      INT64           ``x``      int
      UINT64          ``t``      int
      DOUBLE          ``d``      float
      STRING          ``s``      str
      OBJECT_PATH     ``o``      str
      SIGNATURE       ``g``      str
      ARRAY           ``a``      list
      STRUCT          ``()``     tuple
      VARIANT         ``v``      2-tuple ``(signature, value)``
      DICT_ENTRY      ``{}``     dict (for array of dict entries)
      UNIX_FD         ``h``      (not yet supported)
      ===========    ==========  ===========

   .. automethod:: serialise

.. autoclass:: Header

   .. attribute:: endianness

      :class:`Endianness` object, affecting message serialisation.

   .. attribute:: message_type

      :class:`MessageType` object.

   .. attribute:: flags

      Integer representing message flags. See the D-Bus specification.

   .. attribute:: protocol_version

      Integer, currently always 1.

   .. attribute:: body_length

      Integer, the length of the raw message body in bytes.

   .. attribute:: serial

      Integer, sender's serial number for this message.

   .. attribute:: fields

      Dict, mapping :class:`HeaderFields` values to the relevant Python objects.

Enums
-----

.. class:: Endianness

   .. autoattribute:: little

   .. autoattribute:: big

.. class:: HeaderFields

   .. autoattribute:: path

   .. autoattribute:: interface

   .. autoattribute:: member

   .. autoattribute:: error_name

   .. autoattribute:: reply_serial

   .. autoattribute:: destination

   .. autoattribute:: sender

   .. autoattribute:: signature

   .. autoattribute:: unix_fds

.. class:: MessageType

   .. autoattribute:: method_call

   .. autoattribute:: method_return

   .. autoattribute:: error

   .. autoattribute:: signal
