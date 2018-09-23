"""
Example of subscribing to a D-Bus signal using blocking I/O.
This subscribes to the signal for a desktop notification being closed.

To try it, start this script, then trigger a desktop notification, and close it
somehow to trigger the signal. Use Ctrl-C to stop the script.

This example relies on the ``org.freedesktop.Notifications.NotificationClosed``
signal; some desktops may not support it. See the notification spec for more
details:
https://people.gnome.org/~mccann/docs/notification-spec/notification-spec-latest.html

Match rules are defined in the D-Bus specification:
https://dbus.freedesktop.org/doc/dbus-specification.html#message-bus-routing-match-rules
"""

from jeepney.bus_messages import MatchRule, message_bus
from jeepney.integrate.blocking import connect_and_authenticate, Proxy
from jeepney.wrappers import DBusAddress

noti = DBusAddress('/org/freedesktop/Notifications',
                   bus_name='org.freedesktop.Notifications',
                   interface='org.freedesktop.Notifications')

connection = connect_and_authenticate(bus="SESSION")

match_rule = MatchRule(
    type="signal",
    sender=noti.bus_name,
    interface=noti.interface,
    member="NotificationClosed",
    path=noti.object_path,
)

# This defines messages for talking to the D-Bus bus daemon itself:
session_bus = Proxy(message_bus, connection)

# Tell the session bus to pass us matching signal messages:
print("Match added?", session_bus.AddMatch(match_rule) == ())

reasons = {1: 'expiry', 2: 'dismissal', 3: 'dbus', '4': 'undefined'}
def notification_closed(data):
    """Callback for when we receive a notification closed signal"""
    nid, reason_no = data
    reason = reasons.get(reason_no, 'unknown')
    print('Notification {} closed by: {}'.format(nid, reason))

# Connect the callback to the relevant signal
connection.router.subscribe_signal(
    callback=notification_closed,
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
