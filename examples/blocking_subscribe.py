"""
This example relies on the ``org.freedesktop.Notifications.NotificationClosed``
signal, which may require full Desktop Notifications support.

The following footnote from the ``.ActionInvoked`` section of the
`notification-spec`_ may pertain to this signal as well:

    Clients should not assume the server will generate this signal. Some
    servers may not support user interaction at all, or may not support the
    concept of being able to "invoke" a notification.

See the `match-rules-spec`_ for match-rules details.

.. _notification-spec: https://people.gnome.org/~mccann/docs/notification-spec/
   notification-spec-latest.html

.. _match-rules-spec: https://dbus.freedesktop.org/doc/dbus-specification.html
   #message-bus-routing-match-rules
"""

from jeepney.integrate.blocking import connect_and_authenticate, Proxy
from jeepney.bus_messages import MatchRule, message_bus
from aio_notify import Notifications


noti = Notifications()

connection = connect_and_authenticate(bus="SESSION")

match_rule = MatchRule(
    type="signal",
    sender=noti.bus_name,
    interface=noti.interface,
    member="NotificationClosed",
    path=noti.object_path,
)

session_bus = Proxy(message_bus, connection)
# Pre-made DBus msggen ^~~~~~~~

print("Match added?", session_bus.AddMatch(match_rule) == ())

connection.router.subscribe_signal(
    callback=print,
    path=noti.object_path,
    interface=noti.interface,
    member="NotificationClosed"
)

# Using dbus-send or d-feet or blocking_notify.py, send a notification and
# manually close it or call ``.CloseNotification`` after a beat.
try:
    while True:
        connection.recv_messages()
except KeyboardInterrupt:
    pass
