Jeepney |version|
=================

Jeepney is a pure Python interface to D-Bus, a protocol for interprocess
communication on desktop Linux (mostly).

The core of Jeepney is `I/O free <https://sans-io.readthedocs.io/>`__, and the
``jeepney.integrate`` package contains bindings for different event loops to
handle I/O. Jeepney tries to be *non-magical*, so you may have to write a bit
more code than with other interfaces such as `dbus-python <https://pypi.python.org/pypi/dbus-python>`_
or `pydbus <https://github.com/LEW21/pydbus>`_.

Contents:

.. toctree::
   :maxdepth: 2

   integrate
   bindgen

.. seealso::

   `D-Feet <https://wiki.gnome.org/Apps/DFeet>`__
     App for exploring available D-Bus services on your machine.

   `D-Bus Specification <https://dbus.freedesktop.org/doc/dbus-specification.html>`__
     Technical details about the D-Bus protocol.



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

